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
        
        selected = [
            i for i in range(len(self.chromosome.services))
            if self.chromosome.service[i] == 1
        ]
        
        if not selected:
            logger.warning("no_services_selected")
            return {
                "Status": "no_services",
                "profit": 0,
                "coverage": 0
            }
            
        prob = pulp.LpProblem("Shipping", pulp.LpMaximize)
        
        demand_vars = {}
        for d_idx, demand in enumerate(self.problem.demands):
            demand_vars[d_idx] = pulp.LpVariable(
                f"demand_{d_idx}",
                lowBound = 0,
                upBound = demand.weekly_teu,
                cat=pulp.LpContinuous
            )
        revenue = pulp.lpSum([
            demand.revenue_per_teu * demand_vars[d_idx]
            for d_idx, demand in enumerate(self.problem.demands)
        ])
        
        cost = sum(
            self.problem.services[s].weekly_cost * self.chromosome.frequencies[s]
            for s in selected
        )
        
        prob += revenue - cost, "Profit"
        
        total_capacity = sum(
            self.problem.services[s].capicity * self.chromosome.frequencies[s]
            for s in selected
        )