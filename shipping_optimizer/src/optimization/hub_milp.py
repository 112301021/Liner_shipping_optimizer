import pulp
from collections import defaultdict


class HubMILP:

    def __init__(self, problem, chromosome,
                 max_services_per_demand=10,
                 max_transfer_pairs=40):

        self.problem = problem
        self.chromosome = chromosome
        self.max_services_per_demand = max_services_per_demand
        self.max_transfer_pairs = max_transfer_pairs

        # --------------------------------
        # Pre-index services by port
        # --------------------------------
        self.port_services = defaultdict(list)

        for s_idx, service in enumerate(problem.services):

            if chromosome["services"][s_idx] == 0:
                continue

            for p in service.ports:
                self.port_services[p].append(s_idx)

    # ------------------------------------------------
    # Direct compatibility (fast)
    # ------------------------------------------------
    def compatible_services(self):

        compat = defaultdict(list)

        for d_idx, demand in enumerate(self.problem.demands):

            origin_services = set(
                self.port_services.get(demand.origin, [])
            )

            dest_services = set(
                self.port_services.get(demand.destination, [])
            )

            candidate_services = origin_services & dest_services

            for s_idx in candidate_services:

                ports = self.problem.services[s_idx].ports

                # correct order constraint
                if ports.index(demand.origin) or ports.index(demand.destination):

                    compat[d_idx].append(s_idx)

            # limit services per demand
            compat[d_idx] = compat[d_idx][: self.max_services_per_demand]

        return compat

    # ------------------------------------------------
    # Hub transfer pairs (s1 → hub → s2)
    # ------------------------------------------------
    def transfer_pairs(self):

        pairs = []

        active_services = [
            i for i, s in enumerate(self.chromosome["services"]) if s
        ]

        for s1 in active_services:

            ports1 = set(self.problem.services[s1].ports)

            for s2 in active_services:

                if s1 == s2:
                    continue

                ports2 = set(self.problem.services[s2].ports)

                hubs = ports1 & ports2

                for hub in hubs:

                    pairs.append((s1, s2, hub))

        # prune pairs (optimization trick)
        return pairs[: self.max_transfer_pairs]

    # ------------------------------------------------
    # Solve MILP
    # ------------------------------------------------
    def solve(self):

        prob = pulp.LpProblem(
            "ShippingOptimization",
            pulp.LpMaximize
        )

        compat = self.compatible_services()

        transfer_pairs = self.transfer_pairs()

        flow = {}
        transfer_flow = {}

        # --------------------------------
        # Direct flow variables
        # --------------------------------
        for d, services in compat.items():

            for s in services:

                flow[(d, s)] = pulp.LpVariable(
                    f"x_{d}_{s}",
                    lowBound=0
                )

        # --------------------------------
        # Transfer flow variables
        # --------------------------------
        for d_idx, demand in enumerate(self.problem.demands):

            for s1, s2, hub in transfer_pairs:

                svc1 = self.problem.services[s1]
                svc2 = self.problem.services[s2]

                if demand.origin in svc1.ports or demand.destination in svc2.ports:

                    transfer_flow[(d_idx, s1, s2)] = pulp.LpVariable(
                        f"t_{d_idx}_{s1}_{s2}",
                        lowBound=0
                    )

        # --------------------------------
        # Objective
        # --------------------------------
        revenue = pulp.lpSum(
            self.problem.demands[d].revenue_per_teu * flow[(d, s)]
            for (d, s) in flow
        )

        revenue += pulp.lpSum(
            self.problem.demands[d].revenue_per_teu *
            transfer_flow[(d, s1, s2)]
            for (d, s1, s2) in transfer_flow
        )

        operating_cost =sum(
            self.problem.services[s].weekly_cost *
            self.chromosome["frequencies"][s]
            for s in range(len(self.problem.services))
            if self.chromosome["services"][s]
        )

        profit_expr = revenue - operating_cost

        prob += profit_expr
        prob += profit_expr >= 0

        # --------------------------------
        # Demand constraints
        # --------------------------------
        for d, demand in enumerate(self.problem.demands):

            prob += (

                pulp.lpSum(
                    flow[(d, s)]
                    for s in compat.get(d, [])
                )

                +

                pulp.lpSum(
                    transfer_flow[(d2, s1, s2)]
                    for (d2, s1, s2) in transfer_flow
                    if d2 == d
                )

                <= demand.weekly_teu
            )

        # --------------------------------
        # Service capacity constraints
        # --------------------------------
        for s in range(len(self.problem.services)):

            if not self.chromosome["services"][s]:
                continue

            capacity = (
                self.problem.services[s].capacity *
                self.chromosome["frequencies"][s]
            )

            prob += (

                pulp.lpSum(
                    flow[(d, s)]
                    for (d, s2) in flow
                    if s2 == s
                )

                +

                pulp.lpSum(
                    transfer_flow[(d, s1, s2)]
                    for (d, s1, s2) in transfer_flow
                    if s1 == s or s2 == s
                )

                <= capacity
            )

        # --------------------------------
        # Solve
        # --------------------------------
        prob.solve(
            pulp.PULP_CBC_CMD(msg=0, timeLimit=120)
        )

        # --------------------------------
        # Results
        # --------------------------------
        prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=120))

        profit = pulp.value(prob.objective)

        satisfied = sum(
            pulp.value(v) for v in flow.values()
        )

        total_demand = sum(
            d.weekly_teu for d in self.problem.demands
        )

        coverage = satisfied / total_demand * 100 if total_demand else 0

        return {
            "status": pulp.LpStatus[prob.status],
            "profit": float(profit),
            "coverage": float(coverage),
            "satisfied_demand": float(satisfied),
            "cost": float(operating_cost),
            "num_variables": len(flow),
            "num_services_used": sum(self.chromosome["services"])
        }