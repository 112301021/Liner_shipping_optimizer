from typing import Dict, Any
import time
from src.agents.base import BaseAgent
from src.agents.service_generator_agent import ServiceGeneratorAgent

from src.optimization.data import Problem, Service
from src.optimization.hierarchical_ga import HierarchicalGA
from src.optimization.hub_milp import HubMILP

from src.services.hub_detector import HubDetector

from src.utils.logger import logger


class RegionalAgent(BaseAgent):

    def __init__(self, name: str, region: str, model: str):

        super().__init__(
            name=name,
            role=f"Regional Optimizer - {region}",
            model=model
        )

        self.region = region


    # ------------------------------------------------
    # System Prompt
    # ------------------------------------------------
    def get_system_prompt(self) -> str:

        return f"""
You are a {self.region} shipping network optimization agent.

Your responsibilities:
- Analyze regional shipping demand
- Design efficient liner services
- Maximize weekly profit
- Maintain strong demand coverage

Focus on hub-and-spoke network design and efficient vessel utilization.
"""


    # ------------------------------------------------
    # Hub-based decomposition
    # ------------------------------------------------
    def split_by_hubs(self, problem, num_hubs=5):

        hub_detector = HubDetector(problem)

        hubs = hub_detector.detect_hubs(top_k=num_hubs)

        clusters = {h: [] for h in hubs}

        for p in problem.ports:

            closest_hub = min(
                hubs,
                key=lambda h: problem.distance_matrix.get(h, {}).get(p.id, 1e9)
            )

            clusters[closest_hub].append(p)

        return clusters


    # ------------------------------------------------
    # Main optimization pipeline
    # ------------------------------------------------
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()

        logger.info(
            "regional_agent_started",
            agent=self.name,
            region=self.region
        )

        problem: Problem = input_data["problem"]

        total_demand = sum(d.weekly_teu for d in problem.demands)

        # ---------------------------------------
        # Step 1: LLM strategy
        # ---------------------------------------

        strategy_prompt = f"""
Regional optimization problem.

Region: {self.region}

Ports: {len(problem.ports)}
Demand lanes: {len(problem.demands)}
Total weekly demand: {total_demand:,.0f} TEU

Which network strategy should we prioritize?

a) hub-and-spoke
b) direct services
c) hybrid network
"""

        try:
            strategy = self.call_llm(strategy_prompt, temperature=0.6)
        except Exception:
            strategy = "Hybrid hub-and-spoke network recommended."

        logger.info("regional_strategy_generated")


        # ---------------------------------------
        # Step 2: Generate services
        # ---------------------------------------

        logger.info("service_generation_started")

        service_agent = ServiceGeneratorAgent(
            name="service_generator",
            model=self.model
        )

        service_result = service_agent.process({
            "problem": problem
        })
        
        services = service_result["services"]
        services_generated = len(services)

        # ---------------------------------------
        # Convert dict → Service objects
        # ---------------------------------------

        normalized_services = []

        for i, s in enumerate(services):

            if isinstance(s, Service):
                normalized_services.append(s)

            else:
                normalized_services.append(
                    Service(
                        id=s.get("id", f"svc_{i}"),
                        ports=s["ports"],
                        capacity=s.get("capacity", 5000),
                        weekly_cost=s.get("weekly_cost", 800000),
                        cycle_time=s.get("cycle_time", 28)
                    )
                )

        problem.services = normalized_services

       
        problem.services = normalized_services

        # ---------------------------------------
        # Remove economically unprofitable services
        # ---------------------------------------

        profitable_services = []

        for s in problem.services:

            revenue_estimate = s.capacity * 150  # average revenue per TEU estimate

            if revenue_estimate > s.weekly_cost:
                profitable_services.append(s)

        problem.services = profitable_services

        logger.info(
            "services_generated",
            count=len(problem.services)
        )


        # ---------------------------------------
        # Filter services (speed improvement)
        # ---------------------------------------
        max_services = max(200, int(len(problem.ports) * 0.6))
        services = sorted(
            problem.services,
            key=lambda s: s.capacity / (s.weekly_cost + 1),
            reverse=True
        )[:max_services]

        problem.services = services
        services_filtered = len(services)

        logger.info(
            "services_filtered",
            count=services_filtered
        )
        # ---------------------------------------
        # Step 3: Run GA ONCE for region
        # ---------------------------------------

        logger.info("hierarchical_ga_started")

        ga = HierarchicalGA(problem)
        chromosome = ga.run()

        services_selected = sum(chromosome["services"])

        logger.info(
            "ga_completed",
            services_selected=services_selected
        )

        # ---------------------------------------
        # Step 4: Hub-based MILP decomposition
        # ---------------------------------------

        logger.info("hub_decomposition_started")

        clusters = self.split_by_hubs(problem)

        cluster_results = []

        for hub, ports in clusters.items():

            # Filter demands belonging to cluster
            cluster_port_ids = {p.id for p in ports}
            cluster_demands = [
                d for d in problem.demands
                if d.origin in cluster_port_ids or d.destination in cluster_port_ids
            ]

            if not cluster_demands:
                continue

            sub_problem = Problem(
                ports=ports,
                services=problem.services,
                demands=cluster_demands,
                distance_matrix=problem.distance_matrix
            )

            milp = HubMILP(sub_problem, chromosome)
            milp_result = milp.solve()

            cluster_results.append(milp_result)

        
        # ---------------------------------------
        # Aggregate cluster results
        # ---------------------------------------

        total_profit = sum(r["profit"] for r in cluster_results)

        avg_coverage = (
            sum(r["coverage"] for r in cluster_results) / len(cluster_results)
            if cluster_results else 0
        )

        operating_cost = sum(r.get("cost", 0) for r in cluster_results)

        profit = total_profit
        coverage = avg_coverage

        logger.info(
            "regional_optimization_completed",
            profit=profit,
            coverage=coverage
        )


        # ---------------------------------------
        # Step 4: LLM explanation
        # ---------------------------------------

        explanation_prompt = f"""
Optimization results for {self.region} region.

Services deployed: {services_selected}
Weekly profit: ${profit:,.0f}
Demand coverage: {coverage:.1f}%

Explain whether this is a good shipping network solution in 2 sentences.
"""

        try:
            explanation = self.call_llm(explanation_prompt, temperature=0.6)
        except Exception:
            explanation = "Optimization produced a profitable hub-based shipping network."

        logger.info("solution_explained")


        # ---------------------------------------
        # Final result
        # ---------------------------------------

        result = {

            "agent": self.name,
            "region": self.region,
            "status": "Optimal",

            "services_generated": services_generated,
            "services_filtered": services_filtered,

            "services_selected": services_selected,

            "weekly_profit": profit,
            "coverage_percent": coverage,
            "operating_cost": operating_cost,

            "strategy": strategy,
            "explanation": explanation
        }

        logger.info(
            "regional_agent_complete",
            region=self.region,
            profit=profit,
            coverage=coverage
        )
        regional_runtime = time.perf_counter() - start_time
        return result