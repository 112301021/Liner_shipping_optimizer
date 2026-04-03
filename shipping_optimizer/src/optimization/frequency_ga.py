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
from typing import List

logger = logging.getLogger(__name__)

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
        """
        route_demand = [0.0] * self.num_services
        for i in self.active_idx:
            svc      = self.problem.services[i]
            port_set = set(svc.ports)
            for d in self.problem.demands:
                if d.origin in port_set and d.destination in port_set:
                    route_demand[i] += d.weekly_teu
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
        # ── Fleet constraint penalty (NEW) ───────────────────────────
        import math

        FLEET_SIZE = 300  # you can move this to config later

        vessels_used = sum(
            math.ceil(self.problem.services[i].cycle_time * f / 7)
            for i, f in enumerate(freq)
            if f > 0 and self.services[i] == 1
        )

        if vessels_used > FLEET_SIZE:
            fleet_penalty = (vessels_used - FLEET_SIZE) * 100000
        else:
            fleet_penalty = 0

        return revenue - operating_cost -transship_cost- overcap_penalty - fleet_penalty

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

        for _ in range(self.generations):
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

            if no_improve >= 15:
                break

        best = population[int(np.argmax(fitness))]
        logger.info("frequency_ga_complete", best_fitness=best_fitness)
        return best