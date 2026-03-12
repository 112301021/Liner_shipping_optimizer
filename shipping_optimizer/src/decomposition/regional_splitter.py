from copy import deepcopy


class RegionalSplitter:

    def __init__(self, problem):

        self.problem = problem

    def build_region(self, port_ids):

        """
        Build a regional subproblem.
        """

        port_set = set(port_ids)

        # --------------------------
        # Filter ports
        # --------------------------

        ports = [
            p for p in self.problem.ports
            if p.id in port_set
        ]

        # --------------------------
        # Filter demands
        # --------------------------

        demands = [
            d for d in self.problem.demands
            if (d.origin in port_set or d.destination in port_set)
        ]

        # --------------------------
        # Filter services
        # --------------------------

        services = []

        for s in self.problem.services:

            if any(p in port_set for p in s.ports):

                services.append(deepcopy(s))

        # --------------------------
        # Build regional problem
        # --------------------------

        regional_problem = deepcopy(self.problem)

        regional_problem.ports = ports
        regional_problem.demands = demands
        regional_problem.services = services

        return regional_problem

    def split(self, clusters):

        """
        Split global problem into regional problems.
        """

        regional_problems = {}

        for cluster_id, port_ids in clusters.items():

            regional_problems[cluster_id] = self.build_region(port_ids)

        return regional_problems