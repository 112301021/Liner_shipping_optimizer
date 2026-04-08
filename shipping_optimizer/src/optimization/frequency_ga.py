"""
frequency_ga.py  — Route-Level Frequency Optimisation GA
==========================================================
Fixes applied vs. original:
  1. Frequency is determined per-service from actual corridor demand
     (not global demand), matching supply to demand at route granularity.
  2. optimal_freq = ceil(route_demand / service_capacity), capped at max_freq.
  3. GA refines around the analytical estimate rather than starting blind.
  4. Overcapacity penalty (unused slots cost money) is included in fitness.
  5. All parameters are configurable.
"""

import math
import random
import logging
import numpy as np
import time
from typing import List

logger = logging.getLogger(__name__)

# Phase-1.5 Control Optimizations - Step 1
NO_IMPROVE_LIMIT = 8      # Reduced early stop threshold
MAX_RUNTIME = 90          # Hard runtime cap in seconds

MAX_FREQ = 3          # maximum sailings per week per service
MIN_FREQ = 1


class FrequencyGA:
    def __init__(
        self,
        problem,
        services: List[int],    # binary mask from ServiceGA
        max_freq: int = MAX_FREQ,
        pop_size: int = 40,
        generations: int = 60,
        overcap_penalty: float = 0.015,   # fraction of unused capacity × weekly_cost
    ):
        self.problem    = problem
        self.services   = services        # binary mask
        self.max_freq   = max_freq
        self.pop_size   = pop_size
        self.generations = generations
        self.beta       = overcap_penalty

        self.num_services = len(services)
        self.active_idx   = [i for i, v in enumerate(services) if v == 1]

        # PERFORMANCE OPTIMIZATION: Get pre-computed port sets from problem if available
        if hasattr(problem, 'service_port_sets'):
            self.service_port_sets = problem.service_port_sets
        else:
            self.service_port_sets = [set(svc.ports) for svc in problem.services]

        # ── Route-level demand for each service ──────────────────────
        self.route_demand = self._compute_route_demand()
        # ── Analytical starting frequency for each service ───────────
        self.init_freq    = self._analytical_frequency()

    # ------------------------------------------------------------------ #
    #  Route-level demand computation                                       #
    # ------------------------------------------------------------------ #
    def _compute_route_demand(self) -> List[float]:
        """
        For each active service, sum the weekly TEU of demands where
        BOTH origin and destination are in the service's port list.

        PERFORMANCE OPTIMIZATION: Use pre-computed port sets and demand grouping
        """
        route_demand = [0.0] * self.num_services

        # Pre-group demands by origin for faster lookup
        demand_by_origin = {}
        for d in self.problem.demands:
            demand_by_origin.setdefault(d.origin, []).append(d)

        # For each active service, check demands efficiently
        for i in self.active_idx:
            port_set = self.service_port_sets[i]
            total = 0.0

            # Only check demands originating from ports in the service
            for port in port_set:
                for d in demand_by_origin.get(port, []):
                    if d.destination in port_set:
                        total += d.weekly_teu

            route_demand[i] = total

        return route_demand

    # ------------------------------------------------------------------ #
    #  Analytical frequency estimate                                        #
    # ------------------------------------------------------------------ #
    def _analytical_frequency(self) -> List[int]:
        """
        optimal_freq_i = clamp( ceil( route_demand_i / capacity_i ), 1, max_freq )
        Services with zero demand get frequency 0 (inactive).
        """
        freq = [0] * self.num_services
        for i in self.active_idx:
            demand   = self.route_demand[i]
            capacity = self.problem.services[i].capacity or 1
            if demand > 0:
                raw  = math.ceil(demand / capacity)
                freq[i] = max(MIN_FREQ, min(self.max_freq, raw))
        return freq

    # ------------------------------------------------------------------ #
    #  Population initialisation                                            #
    # ------------------------------------------------------------------ #
    def _random_freq(self) -> List[int]:
        """
        Start near the analytical solution and jitter by ±1.
        """
        freq = list(self.init_freq)
        for i in self.active_idx:
            jitter  = random.randint(-1, 1)
            freq[i] = max(0, min(self.max_freq, freq[i] + jitter))
        return freq

    # ------------------------------------------------------------------ #
    #  Fitness                                                              #
    # ------------------------------------------------------------------ #
    def _evaluate(self, freq: List[int]) -> float:
        """
        fitness = revenue − operating_cost − overcapacity_penalty

        revenue = Σ_i min(capacity_i × freq_i, route_demand_i) × avg_rev/teu
        """
        # ── FIX 1: Early fleet rejection BEFORE expensive computation ──
        FLEET_SIZE = 300
        vessels_used_early = sum(
            math.ceil(self.problem.services[i].cycle_time * f / 7)
            for i, f in enumerate(freq)
            if f > 0 and self.services[i] == 1
        )
        if vessels_used_early > FLEET_SIZE:
            return -1e9  # reject immediately — skip full evaluation

        total_capacity  = 0.0
        satisfied       = 0.0
        operating_cost  = 0.0

        avg_rev = (
            sum(d.weekly_teu * d.revenue_per_teu for d in self.problem.demands)
            / (sum(d.weekly_teu for d in self.problem.demands) or 1.0)
        )

        for i, f in enumerate(freq):
            if f == 0 or self.services[i] == 0:
                continue
            svc       = self.problem.services[i]
            cap       = svc.capacity * f * (7 / (svc.cycle_time or 7))
            demand_i  = self.route_demand[i]
            served_i  = min(cap, demand_i)

            satisfied      += served_i
            total_capacity += cap
            operating_cost += svc.weekly_cost * f

        revenue           = satisfied * avg_rev
        unused_cap        = max(0.0, total_capacity - satisfied)
        overcap_penalty   = self.beta * unused_cap * (operating_cost / (total_capacity or 1))
        
        num_ports = len(self.problem.ports)
        num_hubs  = max(1, int(0.1 * num_ports))

        hub_ratio = min(0.7, max(0.3, num_hubs / num_ports))

        transship_cost = hub_ratio * satisfied * self.problem.demands[0].revenue_per_teu * 0.05

        # Fleet already checked at top — no penalty needed here
        return revenue - operating_cost - transship_cost - overcap_penalty

    # ------------------------------------------------------------------ #
    #  GA loop                                                              #
    # ------------------------------------------------------------------ #
    def run(self) -> List[int]:
        if not self.active_idx:
            return [0] * self.num_services

        population = [self._random_freq() for _ in range(self.pop_size)]
        fitness    = [self._evaluate(p) for p in population]
        best_fitness = max(fitness)
        no_improve   = 0

        # Phase-1.5: Track start time for runtime cap
        start_time = time.time()

        for gen in range(self.generations):
            # Phase-1.5: Check runtime cap
            if time.time() - start_time > MAX_RUNTIME:
                logger.info(f"frequency_ga_runtime_cap gen={gen} best_fitness={best_fitness}")
                break
            ranked     = sorted(zip(population, fitness), key=lambda x: x[1], reverse=True)
            population = [x[0] for x in ranked[:10]]

            while len(population) < self.pop_size:
                p1    = random.choice(ranked[:20])[0]
                child = p1.copy()
                # mutate one active service frequency
                if self.active_idx:
                    idx         = random.choice(self.active_idx)
                    child[idx]  = random.randint(0, self.max_freq)
                population.append(child)

            fitness      = [self._evaluate(p) for p in population]
            current_best = max(fitness)

            if current_best > best_fitness:
                best_fitness = current_best
                no_improve   = 0
            else:
                no_improve += 1

            # Phase-1.5: Reduced early stop threshold
            if no_improve >= NO_IMPROVE_LIMIT:
                logger.info(f"frequency_ga_early_stop gen={gen} best_fitness={best_fitness}")
                break

        best = population[int(np.argmax(fitness))]
        logger.info(f"frequency_ga_complete best_fitness={best_fitness}")
        return best