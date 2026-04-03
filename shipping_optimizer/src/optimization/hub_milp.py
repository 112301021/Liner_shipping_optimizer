"""
hub_milp.py  — Enhanced MILP Flow Optimiser
=============================================
Critical fixes:
  1. max_transfer_pairs default raised to 2000.
  2. Transfer pair enumeration prioritises by DEMAND VOLUME at hub
     so highest-impact transshipments always make it within the cap.
  3. min_coverage default = 0.0 (was 0.30, infeasible with sparse pools).
  4. Coverage driven by alpha_unserved penalty ($300/TEU default).
  5. Single MILP solve. Full cost breakdown output.
"""

import logging
import pulp
from collections import defaultdict
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

DEFAULT_TRANSSHIP_COST = 80.0
DEFAULT_PORT_COST      = 15.0
DEFAULT_PORT_CAPACITY  = 1e9
DEFAULT_MIN_COVERAGE   = 0.0    # penalty-driven, not constraint-driven


class HubMILP:
    def __init__(
        self,
        problem,
        chromosome,
        max_services_per_demand: int  = 10,
        max_transfer_pairs: int       = 2000,  # RAISED: essential for hub routing
        transship_cost_per_teu: float = DEFAULT_TRANSSHIP_COST,
        port_cost_per_teu: float      = DEFAULT_PORT_COST,
        port_capacity: float          = DEFAULT_PORT_CAPACITY,
        min_coverage: float           = DEFAULT_MIN_COVERAGE,
        w_profit: float               = 0.5,
        w_coverage: float             = 0.4,
        alpha_unserved: float         = 300.0,  # RAISED: $300 >> operating cost/TEU
        time_limit: int               = 120,
        fleet_size: int = 300,
    ):
        self.problem    = problem
        self.chromosome = chromosome

        self.max_svc_per_demand = max_services_per_demand
        self.max_xfer_pairs     = max_transfer_pairs
        self.tc_per_teu         = transship_cost_per_teu
        self.pc_per_teu         = port_cost_per_teu
        self.port_capacity      = port_capacity
        self.min_coverage       = min_coverage
        self.w_profit           = w_profit
        self.w_coverage         = w_coverage
        self.alpha              = alpha_unserved
        self.time_limit         = time_limit
        self.fleet_size         = fleet_size

        self.port_lookup: Dict = {p.id: p for p in problem.ports}

        # Index active services by port
        self.port_services: Dict[int, List[int]] = defaultdict(list)
        services_mask = chromosome.get("services", [])
        for s_idx, svc in enumerate(problem.services):
            if s_idx >= len(services_mask) or services_mask[s_idx] == 0:
                continue
            for p in svc.ports:
                self.port_services[p].append(s_idx)

        # Pre-compute port demand for transfer pair prioritisation
        self._port_demand: Dict[int, float] = defaultdict(float)
        for d in problem.demands:
            self._port_demand[d.origin]      += d.weekly_teu
            self._port_demand[d.destination] += d.weekly_teu

        demand_score = defaultdict(float)
        for d in problem.demands:
            demand_score[d.origin] += d.weekly_teu
            demand_score[d.destination] += d.weekly_teu

        self.port_capacity_map = {
            p.id: 50000 + 0.1 * demand_score[p.id]
            for p in problem.ports
        }
    
    def _vessels_required(self, service, freq):
        import math
        return math.ceil(service.cycle_time * freq / 7)
    
    def _port_handling_cost(self, port_id: int) -> float:
        port = self.port_lookup.get(port_id)
        hc   = getattr(port, "handling_cost", 0.0) if port else 0.0
        return hc + self.pc_per_teu

    def _port_cap(self, port_id: int) -> float:
        return self.port_capacity_map.get(port_id, 50000)

    # ------------------------------------------------------------------ #
    #  Compatible services for direct satisfaction                          #
    # ------------------------------------------------------------------ #
    def compatible_services(self) -> Dict[int, List[int]]:
        compat: Dict[int, List[int]] = defaultdict(list)
        for d_idx, demand in enumerate(self.problem.demands):
            origin_svc = set(self.port_services.get(demand.origin, []))
            dest_svc   = set(self.port_services.get(demand.destination, []))
            candidates = origin_svc & dest_svc

            valid = []
            for s_idx in candidates:
                ports = self.problem.services[s_idx].ports
                try:
                    o_pos = ports.index(demand.origin)
                    d_pos = ports.index(demand.destination)
                    if o_pos < d_pos:
                        valid.append(s_idx)
                except ValueError:
                    pass
            compat[d_idx] = valid[: self.max_svc_per_demand]
        return compat

    # ------------------------------------------------------------------ #
    #  Transfer pairs — demand-volume prioritised                           #
    # ------------------------------------------------------------------ #
    def transfer_pairs(self) -> List[Tuple[int, int, int]]:
        """
        Enumerate (s1, s2, hub) pairs where services share a hub port.
        Prioritise by hub demand volume so most impactful pairs are included.
        """
        services_mask = self.chromosome.get("services", [])
        active = [
            i for i, v in enumerate(services_mask)
            if v == 1 and i < len(self.problem.services)
        ]

        seen = set()
        pairs_priority: List[Tuple[float, int, int, int]] = []

        for s1 in active:
            p1 = set(self.problem.services[s1].ports)
            for s2 in active:
                if s1 == s2:
                    continue
                p2   = set(self.problem.services[s2].ports)
                hubs = p1 & p2
                for hub in hubs:
                    key = (s1, s2, hub)
                    if key in seen:
                        continue
                    seen.add(key)
                    priority = self._port_demand.get(hub, 0.0)
                    pairs_priority.append((-priority, s1, s2, hub))

        pairs_priority.sort()
        return [
            (s1, s2, hub)
            for _, s1, s2, hub in pairs_priority[: self.max_xfer_pairs]
        ]

    # ------------------------------------------------------------------ #
    #  Solve MILP — single call                                             #
    # ------------------------------------------------------------------ #
    def solve(self) -> Dict:
        prob   = pulp.LpProblem("ShippingOpt", pulp.LpMaximize)
        compat = self.compatible_services()
        xfer   = self.transfer_pairs()

        total_demand_teu = sum(d.weekly_teu for d in self.problem.demands)

        # Decision variables
        flow: Dict          = {}
        transfer_flow: Dict = {}

        for d, svcs in compat.items():
            for s in svcs:
                flow[(d, s)] = pulp.LpVariable(f"x_{d}_{s}", lowBound=0)

        for d_idx, demand in enumerate(self.problem.demands):
            for s1, s2, hub in xfer:
                svc1 = self.problem.services[s1]
                svc2 = self.problem.services[s2]
                if demand.origin in svc1.ports and demand.destination in svc2.ports:
                    key = (d_idx, s1, s2)
                    if key not in transfer_flow:
                        transfer_flow[key] = pulp.LpVariable(
                            f"t_{d_idx}_{s1}_{s2}", lowBound=0
                        )

        unserved = {
            d: pulp.LpVariable(f"u_{d}", lowBound=0)
            for d in range(len(self.problem.demands))
        }

        # Revenue (actual satisfied demand only)
        revenue = pulp.lpSum(
            self.problem.demands[d].revenue_per_teu * flow[(d, s)]
            for (d, s) in flow
        ) + pulp.lpSum(
            self.problem.demands[d].revenue_per_teu * transfer_flow[(d, s1, s2)]
            for (d, s1, s2) in transfer_flow
        )

        # Operating cost (fixed)
        services_mask = self.chromosome.get("services", [])
        frequencies   = self.chromosome.get("frequencies", [])
        operating_cost = sum(
            self.problem.services[s].weekly_cost * max(1, frequencies[s] if s < len(frequencies) else 1)
            for s in range(len(self.problem.services))
            if s < len(services_mask) and services_mask[s]
        )

        # Transshipment cost
        transship_cost = pulp.lpSum(
            self.tc_per_teu * transfer_flow[(d, s1, s2)]
            for (d, s1, s2) in transfer_flow
        )

        # Port handling cost
        port_flow_direct: Dict[int, List] = defaultdict(list)
        for (d, s), var in flow.items():
            for p in self.problem.services[s].ports:
                port_flow_direct[p].append(var)

        port_handling_cost = pulp.lpSum(
            self._port_handling_cost(p) * pulp.lpSum(vars_)
            for p, vars_ in port_flow_direct.items()
        )

        # Unserved demand penalty — RAISED to $300/TEU to force coverage
        unserved_penalty = self.alpha * pulp.lpSum(unserved.values())

        profit_expr = (
            revenue - operating_cost - transship_cost
            - port_handling_cost - unserved_penalty
        )

        satisfied_expr = (
            pulp.lpSum(flow.values())
            + pulp.lpSum(transfer_flow.values())
        )
        coverage_reward = (
            (self.w_coverage / max(self.w_profit, 1e-6))
            * (satisfied_expr / max(total_demand_teu, 1.0))
            * abs(operating_cost + 1)
        )

        prob += profit_expr + coverage_reward
        
        # ─────────────────────────────────────────────
        # Fleet constraint (NEW)
        # ─────────────────────────────────────────────
        services_mask = self.chromosome.get("services", [])
        frequencies   = self.chromosome.get("frequencies", [])

        total_vessels_used = sum(
            self._vessels_required(self.problem.services[s],
                                max(1, frequencies[s] if s < len(frequencies) else 1))
            for s in range(len(self.problem.services))
            if s < len(services_mask) and services_mask[s]
        )

        # Convert to constant constraint (since freq is fixed from GA)
        #prob += total_vessels_used <= self.fleet_size

        # Constraints
        for d, demand in enumerate(self.problem.demands):
            prob += (
                pulp.lpSum(flow[(d, s)] for s in compat.get(d, []))
                + pulp.lpSum(
                    transfer_flow[(d2, s1, s2)]
                    for (d2, s1, s2) in transfer_flow if d2 == d
                )
                + unserved[d]
                == demand.weekly_teu
            )

        if self.min_coverage > 0:
            prob += satisfied_expr >= self.min_coverage * total_demand_teu

        for s in range(len(self.problem.services)):
            if s >= len(services_mask) or not services_mask[s]:
                continue
            freq     = max(1, frequencies[s] if s < len(frequencies) else 1)
            svc = self.problem.services[s]
            capacity = self.problem.services[s].capacity * freq * (7 / (svc.cycle_time or 7))
            prob += (
                pulp.lpSum(flow[(d, s)] for (d, s2) in flow if s2 == s)
                + pulp.lpSum(
                    transfer_flow[(d, s1, s2)]
                    for (d, s1, s2) in transfer_flow if s1 == s or s2 == s
                )
                <= capacity
            )

        for p, vars_ in port_flow_direct.items():
            prob += pulp.lpSum(vars_) <= self._port_cap(p)

        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=self.time_limit)
        prob.solve(solver)

        status              = pulp.LpStatus[prob.status]
        import math
        services_mask = self.chromosome.get("services", [])
        frequencies   = self.chromosome.get("frequencies", [])

        total_vessels_used = sum(
            math.ceil(self.problem.services[s].cycle_time * freq / 7)
            for s, freq in enumerate(frequencies)
            if s < len(services_mask) and services_mask[s]
        )

        if total_vessels_used > self.fleet_size:
            logger.warning(
                "fleet_constraint_violated | used=%d limit=%d",
                total_vessels_used,
                self.fleet_size
            )
        profit_v            = pulp.value(prob.objective) or 0.0
        direct_satisfied    = sum(pulp.value(v) or 0.0 for v in flow.values())
        transship_satisfied = sum(pulp.value(v) or 0.0 for v in transfer_flow.values())
        total_satisfied     = direct_satisfied + transship_satisfied
        unserved_teu        = sum(pulp.value(v) or 0.0 for v in unserved.values())
        coverage            = total_satisfied / total_demand_teu * 100 if total_demand_teu else 0.0
        transship_cost_v    = sum(
            self.tc_per_teu * (pulp.value(v) or 0.0) for v in transfer_flow.values()
        )
        port_cost_v = sum(
            self._port_handling_cost(p) * sum(pulp.value(v) or 0.0 for v in vars_)
            for p, vars_ in port_flow_direct.items()
        )
        total_cost_v = operating_cost + transship_cost_v + port_cost_v

        logger.info(
            "milp_solved",
            status=status, profit=round(profit_v, 2), coverage=round(coverage, 2),
            direct_teu=round(direct_satisfied, 2),
            transship_teu=round(transship_satisfied, 2),
            transfer_pairs=len(transfer_flow),
            unserved=round(unserved_teu, 2),
        )

        return {
            "status":            status,
            "profit":            float(profit_v),
            "cost":              float(operating_cost),
            "transship_cost":    float(transship_cost_v),
            "port_cost":         float(port_cost_v),
            "total_cost":        float(total_cost_v),
            "coverage":          float(coverage),
            "satisfied_demand":  float(total_satisfied),
            "direct_demand":     float(direct_satisfied),
            "transship_demand":  float(transship_satisfied),
            "total_demand":      float(total_demand_teu),
            "unserved_demand":   float(unserved_teu),
            "num_direct_vars":   len(flow),
            "num_transfer_vars": len(transfer_flow),
            "num_services_used": sum(
                1 for s in range(len(services_mask)) if services_mask[s]
            ),
        }