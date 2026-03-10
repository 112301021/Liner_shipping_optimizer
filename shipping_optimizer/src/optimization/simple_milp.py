import pulp
from typing import Dict

from src.optimization.data import Problem
from src.optimization.simple_ga import Chromosome
from src.utils.config import Config
from src.utils.logger import logger


class SimpleMilp:

    def __init__(self, problem: Problem, chromosome: Chromosome):

        self.problem = problem
        self.chromosome = chromosome

    def solve(self) -> Dict:

        logger.info("milp_started")

        selected_services = [
            i for i in range(len(self.chromosome.services))
            if self.chromosome.services[i] == 1
        ]

        if not selected_services:

            logger.warning("no_services_selected")

            return {
                "status": "no_services",
                "profit": 0,
                "coverage": 0
            }

        prob = pulp.LpProblem("LinerShippingOptimization", pulp.LpMaximize)

        # -----------------------------
        # Demand variables
        # -----------------------------
        demand_vars = {}

        for d_idx, demand in enumerate(self.problem.demands):

            demand_vars[d_idx] = pulp.LpVariable(
                f"demand_{d_idx}",
                lowBound=0,
                upBound=demand.weekly_teu
            )

        # -----------------------------
        # Service utilization variables
        # -----------------------------
        service_load = {}

        for s in selected_services:

            service_load[s] = pulp.LpVariable(
                f"service_load_{s}",
                lowBound=0
            )

        # -----------------------------
        # Objective
        # -----------------------------
        revenue = pulp.lpSum(
            demand.revenue_per_teu * demand_vars[d_idx]
            for d_idx, demand in enumerate(self.problem.demands)
        )

        cost = pulp.lpSum(
            self.problem.services[s].weekly_cost *
            self.chromosome.frequencies[s]
            for s in selected_services
        )

        prob += revenue - cost

        # -----------------------------
        # Capacity constraints per service
        # -----------------------------
        for s in selected_services:

            capacity = (
                self.problem.services[s].capacity *
                self.chromosome.frequencies[s]
            )

            prob += (
                service_load[s] <= capacity,
                f"capacity_service_{s}"
            )

        # -----------------------------
        # Total flow balance
        # -----------------------------
        prob += (
            pulp.lpSum(service_load.values()) ==
            pulp.lpSum(demand_vars.values()),
            "flow_balance"
        )

        # -----------------------------
        # Solve
        # -----------------------------
        prob.solve(
            pulp.PULP_CBC_CMD(
                msg=0,
                timeLimit=Config.MILP_TIME_LIMIT
            )
        )

        # -----------------------------
        # Extract results
        # -----------------------------
        if prob.status == pulp.LpStatusOptimal:

            profit = pulp.value(prob.objective)

            satisfied = sum(
                pulp.value(v) for v in demand_vars.values()
            )

            total_demand = sum(
                d.weekly_teu for d in self.problem.demands
            )

            coverage = (
                satisfied / total_demand * 100
                if total_demand > 0 else 0
            )

            total_cost = sum(
                self.problem.services[s].weekly_cost *
                self.chromosome.frequencies[s]
                for s in selected_services
            )

            logger.info(
                "milp_complete",
                status="optimal",
                profit=f"${profit:,.0f}",
                coverage=f"{coverage:.1f}%"
            )

            return {
                "status": "optimal",
                "profit": profit,
                "satisfied_demand": satisfied,
                "total_demand": total_demand,
                "coverage": coverage,
                "num_services": len(selected_services),
                "cost": total_cost
            }

        else:

            logger.warning(
                "milp_failed",
                status=prob.status
            )

            return {
                "status": "failed",
                "profit": 0,
                "coverage": 0
            }