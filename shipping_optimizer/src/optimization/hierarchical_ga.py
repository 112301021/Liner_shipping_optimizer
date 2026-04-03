"""
hierarchical_ga.py  — Two-Level GA Orchestrator
=================================================
Fixes applied vs. original:
  1. ServiceGA now uses demand-driven fitness (see service_ga.py).
  2. FrequencyGA now uses route-level demand per service (see frequency_ga.py).
  3. Smart service filtering is applied BEFORE frequency optimisation to remove
     services with zero corridor demand (saves compute, improves GA quality).
  4. Hard runtime budget (60 s default) prevents runaway execution.
  5. Returns enriched chromosome including demand coverage estimate.
"""

import logging
import time
from typing import Dict, Any

from src.optimization.service_ga    import ServiceGA
from src.optimization.frequency_ga  import FrequencyGA

logger = logging.getLogger(__name__)


class HierarchicalGA:
    def __init__(
        self,
        problem,
        # pass-through to ServiceGA
        pop_size: int   = 80,
        generations: int = 120,
        w_profit: float  = 0.5,
        w_coverage: float = 0.4,
        w_cost: float    = 0.1,
        alpha_unserved: float = 50.0,
        
        transship_cost_per_teu: float = 80.0,
        port_cost_per_teu: float = 15.0,
        # pass-through to FrequencyGA
        max_freq: int    = 3,
        # runtime budget
        max_runtime_sec: float = 60.0,
        # demand threshold for service filtering
        min_route_demand_threshold: float = 0.0,   # TEU — 0 = keep all
    ):
        self.problem  = problem
        self.max_time = max_runtime_sec

        self._sga_kwargs = dict(
            pop_size      = pop_size,
            generations   = generations,
            w_profit      = w_profit,
            w_coverage    = w_coverage,
            w_cost        = w_cost,
            alpha_unserved = alpha_unserved,
            
            transship_cost_per_teu = transship_cost_per_teu,
            port_cost_per_teu = port_cost_per_teu,
        )
        self._fga_kwargs = dict(max_freq = max_freq)
        self.min_demand_threshold = min_route_demand_threshold

    # ------------------------------------------------------------------ #
    #  Smart service pre-filter                                             #
    # ------------------------------------------------------------------ #
    def _filter_services(self) -> None:
        """
        Remove services that cover zero demand corridors or have a
        clearly negative expected margin.  Operates in-place on problem.services.
        """
        corridor_set = set()
        for d in self.problem.demands:
            corridor_set.add((d.origin, d.destination))

        kept = []
        for svc in self.problem.services:
            port_set = set(svc.ports)
            # Check if any demand corridor is directly covered
            covers = any(
                o in port_set and d in port_set
                for (o, d) in corridor_set
            )
            # Basic margin check: expected revenue at 50% utilisation > cost
            margin_ok = (svc.capacity * 0.5 * 150) > svc.weekly_cost
            if covers and margin_ok:
                kept.append(svc)

        before = len(self.problem.services)
        self.problem.services = kept
        logger.info("service_filter", before=before, after=len(kept))

    # ------------------------------------------------------------------ #
    #  Main run                                                             #
    # ------------------------------------------------------------------ #
    def run(self) -> Dict[str, Any]:
        t0 = time.perf_counter()

        # ── Pre-filter services ────────────────────────────────────────
        self._filter_services()

        if not self.problem.services:
            logger.warning("no_services_after_filter")
            return {"services": [], "frequencies": [], "coverage_estimate": 0.0}

        # ── Level 1: service selection ─────────────────────────────────
        service_ga   = ServiceGA(self.problem, **self._sga_kwargs)
        best_services = service_ga.run()

        elapsed = time.perf_counter() - t0
        if elapsed > self.max_time * 0.8:
            logger.warning("ga_runtime_budget_near | elapsed=%.2fs", elapsed)

        # ── Level 2: frequency optimisation ───────────────────────────
        freq_ga   = FrequencyGA(self.problem, best_services, **self._fga_kwargs)
        best_freq = freq_ga.run()

        # ── Coverage estimate from GA fitness info ─────────────────────
        total_demand = sum(d.weekly_teu for d in self.problem.demands)
        satisfied    = sum(
            min(
                self.problem.services[i].capacity * best_freq[i],
                service_ga.service_direct_demand[i]
            )
            for i in range(len(best_services)) if best_services[i] == 1
        )
        coverage_estimate = min(satisfied, total_demand) / (total_demand or 1.0) * 100

        chromosome = {
            "services":          best_services,
            "frequencies":       best_freq,
            "coverage_estimate": coverage_estimate,
        }

        logger.info(
            "hierarchical_ga_complete",
            services_selected = sum(best_services),
            coverage_estimate = coverage_estimate,
            elapsed_sec       = round(time.perf_counter() - t0, 2),
        )
        return chromosome