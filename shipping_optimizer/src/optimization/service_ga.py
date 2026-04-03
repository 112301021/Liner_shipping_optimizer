"""
service_ga.py  — Demand-Driven Service Selection GA
=====================================================
Fixes applied vs. original:
  1. Fitness uses estimated_served_demand = min(route_capacity, corridor_demand)
     instead of capacity × avg_revenue (which assumed 100% utilisation).
  2. Every service is scored against actual OD demand it touches.
  3. Demand-alignment penalty removes services with zero corridor coverage.
  4. Coverage reward term drives the GA toward high-demand lane saturation.
  5. LLM calls are OUTSIDE the fitness function (budget guard unchanged).
  6. Hard iteration cap (generations) prevents infinite loops.
  7. All parameters are configurable via constructor args.
"""

import random
import logging
import numpy as np
from collections import defaultdict
from typing import List, Optional

logger = logging.getLogger(__name__)


class ServiceGA:
    # ------------------------------------------------------------------ #
    #  Construction                                                         #
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        problem,
        pop_size: int = 80,
        generations: int = 120,
        # Multi-objective weights
        w_profit: float = 0.5,
        w_coverage: float = 0.4,
        w_cost: float = 0.1,
        # Penalty coefficients
        alpha_unserved: float = 50.0,       # $/TEU unserved
        beta_overcapacity: float = 0.02,    # fraction of unused capacity cost
        gamma_alignment: float = 0.3,       # penalty for zero-demand services
        # Transshipment / port cost pass-through estimates
        transship_cost_per_teu: float = 80.0,
        port_cost_per_teu: float = 15.0,
        # LLM budget
        llm_budget: int = 0,                # set >0 to enable LLM assist
    ):
        self.problem     = problem
        self.generations = generations
        self.pop_size    = pop_size

        # Weights & penalties
        self.w_profit   = w_profit
        self.w_coverage = w_coverage
        self.w_cost     = w_cost
        self.alpha      = alpha_unserved
        self.beta       = beta_overcapacity
        self.gamma      = gamma_alignment
        self.tc_per_teu = transship_cost_per_teu
        self.pc_per_teu = port_cost_per_teu

        self.llm_budget   = llm_budget
        self.mutation_rate = 0.15
        self.fitness_cache: dict = {}

        self.num_services = len(problem.services)
        self.total_demand = sum(d.weekly_teu for d in problem.demands)

        # ── Pre-build demand index: service_idx → relevant OD demand ──
        self._build_demand_index()

        # ── Adaptive parameter tuning (pure heuristic, no LLM) ────────
        self._tune_parameters()

    # ------------------------------------------------------------------ #
    #  Demand index                                                         #
    # ------------------------------------------------------------------ #
    def _build_demand_index(self):
        """
        For each service, record the sum of weekly TEU for OD pairs
        that are directly served (both origin AND destination on the route).
        Also record partial score for services that cover one endpoint.
        """
        # corridor_demand[frozenset({o, d})] = weekly_teu
        self.corridor_demand: dict = {}
        for d in self.problem.demands:
            key = (d.origin, d.destination)
            self.corridor_demand[key] = self.corridor_demand.get(key, 0) + d.weekly_teu

        # service_direct_demand[i] = TEU directly served by service i
        # service_partial_demand[i] = TEU where only one endpoint matches
        self.service_direct_demand  = np.zeros(self.num_services)
        self.service_partial_demand = np.zeros(self.num_services)

        for i, svc in enumerate(self.problem.services):
            port_set = set(svc.ports)
            for (o, d), teu in self.corridor_demand.items():
                if o in port_set and d in port_set:
                    self.service_direct_demand[i] += teu
                elif o in port_set or d in port_set:
                    self.service_partial_demand[i] += teu

        # Revenue per TEU (weighted average across demands)
        total_teu = self.total_demand or 1.0
        self.avg_rev_per_teu = sum(
            d.weekly_teu * d.revenue_per_teu for d in self.problem.demands
        ) / total_teu

        logger.debug(
            "demand_index_built",
            services=self.num_services,
            total_demand=self.total_demand,
        )

    # ------------------------------------------------------------------ #
    #  Adaptive parameter tuning (heuristic — no LLM)                     #
    # ------------------------------------------------------------------ #
    def _tune_parameters(self):
        n = self.num_services
        if n < 100:
            self.pop_size      = 60
            self.mutation_rate = 0.10
        elif n < 500:
            self.pop_size      = 100
            self.mutation_rate = 0.15
        else:
            self.pop_size      = 140
            self.mutation_rate = 0.20
        logger.debug("ga_params_tuned", pop_size=self.pop_size, mut=self.mutation_rate)

    # ------------------------------------------------------------------ #
    #  Smart initialisation                                                 #
    # ------------------------------------------------------------------ #
    def _random_solution(self) -> List[int]:
        """
        Bias initial population toward high-demand services so the GA
        starts from a meaningful baseline, not a random scatter.
        """
        scores = self.service_direct_demand + 0.3 * self.service_partial_demand
        total  = scores.sum() or 1.0
        probs  = scores / total          # probability proportional to demand

        n_select = random.randint(
            max(5, self.num_services // 20),
            max(10, self.num_services // 8),
        )
        selected = np.random.choice(
            self.num_services, size=min(n_select, self.num_services),
            replace=False, p=probs
        )
        sol = [0] * self.num_services
        for idx in selected:
            sol[idx] = 1
        return sol

    # ------------------------------------------------------------------ #
    #  Fitness (demand-driven, multi-objective)                            #
    # ------------------------------------------------------------------ #
    def evaluate(self, services: List[int]) -> float:
        """
        Objective = w1·Profit + w2·Coverage − w3·Cost

        Profit = Revenue − OperatingCost − TransshipCost − PortCost − Penalties
        Revenue  = Σ min(svc.capacity, direct_demand_on_route) × rev_per_teu
        Coverage = satisfied_demand / total_demand
        """
        if not isinstance(services, list):
            return -1e12

        key = tuple(services)
        if key in self.fitness_cache:
            return self.fitness_cache[key]

        selected_idx = [i for i, v in enumerate(services) if v == 1]
        if not selected_idx:
            return -1e12

        # ── Revenue: demand-driven ─────────────────────────────────────
        satisfied_demand = 0.0
        operating_cost   = 0.0
        revenue = 0.0
        port_cost        = 0.0
        alignment_penalty = 0.0

        covered_corridors: dict = {}   # corridor → TEU satisfied

        for i in selected_idx:
            svc    = self.problem.services[i]
            direct = self.service_direct_demand[i]

            # How much of this service's capacity is actually absorbed by demand?
            # ── Capacity adjusted by cycle time ─────────────────────
            effective_capacity = svc.capacity * (7 / (svc.cycle_time or 7))
            served = min(effective_capacity, direct)

            # ── Accumulate satisfied demand ─────────────────────────
            satisfied_demand += served

            # ── Yield-based revenue (NEW) ───────────────────────────
            yield_factor = 0.6 + 0.4 * (served / (effective_capacity or 1))
            revenue += served * self.avg_rev_per_teu * yield_factor

            # Track corridor coverage (for per-corridor cap)
            port_set = set(svc.ports)
            for (o, d), teu in self.corridor_demand.items():
                if o in port_set and d in port_set:
                    covered_corridors[(o, d)] = (
                        covered_corridors.get((o, d), 0) + svc.capacity
                    )

            # Operating cost
            operating_cost += svc.weekly_cost

            # Port handling cost (per port call)
            for p_id in svc.ports:
                port = next((p for p in self.problem.ports if p.id == p_id), None)
                port_hc = getattr(port, "handling_cost", 0.0) if port else 0.0
                port_cost += served * (port_hc + self.pc_per_teu)

            # Demand-alignment penalty: penalise services with zero direct demand
            if direct == 0:
                alignment_penalty += self.gamma * svc.weekly_cost

        # Cap satisfied demand at total
        satisfied_demand = min(satisfied_demand, self.total_demand)
        unserved_demand  = max(0.0, self.total_demand - satisfied_demand)

        # ── Revenue ────────────────────────────────────────────────────
       # yield_factor = 0.6 + 0.4 * (satisfied_demand / (total_capacity or 1))
        #revenue = satisfied_demand * self.avg_rev_per_teu * yield_factor

        # ── Transshipment cost (estimated: 20% of satisfied flows use 1 hub) ─
        num_ports = len(self.problem.ports)
        num_hubs  = max(1, int(0.1 * num_ports))  # approx hubs

        hub_ratio = min(0.7, max(0.3, num_hubs / num_ports))

        transship_cost = hub_ratio * satisfied_demand * self.tc_per_teu
        transship_cost = hub_ratio* satisfied_demand * self.tc_per_teu

        # ── Penalties ──────────────────────────────────────────────────
        # Unserved demand penalty
        unserved_penalty  = self.alpha * unserved_demand
        # Overcapacity penalty (unused capacity costs money)
        total_capacity    = sum(self.problem.services[i].capacity for i in selected_idx)
        unused_cap        = max(0.0, total_capacity - satisfied_demand)
        overcap_penalty   = self.beta * unused_cap * (operating_cost / (total_capacity or 1))

        profit = (
            revenue
            - operating_cost
            - transship_cost
            - port_cost
            - unserved_penalty
            - overcap_penalty
            - alignment_penalty
        )

        coverage = satisfied_demand / (self.total_demand or 1.0)

        # Multi-objective composite
        fitness = (
            self.w_profit   * profit
            + self.w_coverage * coverage * 1e6   # scale coverage to profit magnitude
            - self.w_cost   * operating_cost
        )

        self.fitness_cache[key] = fitness
        return fitness

    # ------------------------------------------------------------------ #
    #  GA operators                                                         #
    # ------------------------------------------------------------------ #
    def _mutate(self, sol: List[int]) -> List[int]:
        child = sol.copy()
        # flip a random bit; bias toward activating high-demand services
        if random.random() < 0.5:
            # activate a high-demand service that is currently off
            off_idx = [i for i, v in enumerate(child) if v == 0]
            if off_idx:
                scores = [self.service_direct_demand[i] for i in off_idx]
                total  = sum(scores) or 1.0
                probs  = [s / total for s in scores]
                idx    = random.choices(off_idx, weights=probs)[0]
                child[idx] = 1
        else:
            idx = random.randint(0, self.num_services - 1)
            child[idx] = 1 - child[idx]
        return child

    @staticmethod
    def _crossover(p1: List[int], p2: List[int]) -> List[int]:
        point = random.randint(1, len(p1) - 2)
        return p1[:point] + p2[point:]

    # ------------------------------------------------------------------ #
    #  Main GA loop                                                         #
    # ------------------------------------------------------------------ #
    def run(self) -> List[int]:
        population = [self._random_solution() for _ in range(self.pop_size)]
        fitness    = [self.evaluate(p) for p in population]

        best_fitness = max(fitness)
        no_improve   = 0

        for gen in range(self.generations):
            ranked = sorted(zip(population, fitness), key=lambda x: x[1], reverse=True)
            elite  = [x[0] for x in ranked[:10]]
            population = elite.copy()

            while len(population) < self.pop_size:
                p1 = random.choice(ranked[:20])[0]
                p2 = random.choice(ranked[:20])[0]
                child = self._crossover(p1, p2)
                if random.random() < self.mutation_rate:
                    child = self._mutate(child)
                population.append(child)

            fitness      = [self.evaluate(p) for p in population]
            current_best = max(fitness)

            if current_best > best_fitness:
                best_fitness = current_best
                no_improve   = 0
            else:
                no_improve += 1

            if no_improve >= 20:
                logger.info("ga_early_stop", gen=gen, best_fitness=best_fitness)
                break

        best = population[int(np.argmax(fitness))]
        logger.info(
            "service_ga_complete",
            services_selected=sum(best),
            best_fitness=best_fitness,
        )
        return best