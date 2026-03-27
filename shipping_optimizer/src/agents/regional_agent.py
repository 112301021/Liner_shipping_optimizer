from typing import Dict, Any
import time

from src.llm.evaluator import LLMEvaluator
from src.agents.base import BaseAgent
from src.agents.service_generator_agent import ServiceGeneratorAgent

from src.optimization.data import Problem, Service
from src.optimization.optimizer import ServiceOptimizer
from src.optimization.hub_milp import HubMILP

from src.services.hub_detector import HubDetector
from src.utils.logger import logger


class RegionalAgent(BaseAgent):

    def __init__(self, name: str, region: str, model: str, rl_model_path: str = None):

        super().__init__(
            name=name,
            role=f"Regional Optimizer - {region}",
            model=model
        )

        self.region = region
        self.evaluator = LLMEvaluator()

        self.optimizer = ServiceOptimizer(
            use_rl=True,
            rl_model_path=rl_model_path,
            fallback_to_ga=True
        )

    # ------------------------------------------------
    def get_system_prompt(self) -> str:
        return f"""
You are a {self.region} optimization agent.

You adapt based on feedback from orchestrator.
Focus on profit, coverage, and efficiency.
"""

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
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:

        start_time = time.perf_counter()

        problem: Problem = input_data["problem"]
        feedback = input_data.get("feedback", [])  # ✅ receive feedback

        logger.info(
            "regional_agent_started",
            agent=self.name,
            region=self.region,
            feedback=feedback
        )

        # ------------------------------------------------
        # APPLY FEEDBACK (CRITICAL)
        # ------------------------------------------------

        problem = self._apply_feedback(problem, feedback)

        total_demand = sum(d.weekly_teu for d in problem.demands)

        # ---- Strategy ----
        strategy = self._generate_strategy(problem, total_demand)

        # ---- Service Generation ----
        service_agent = ServiceGeneratorAgent(
            name="service_generator",
            model=self.model
        )

        services = service_agent.process({"problem": problem})["services"]

        problem.services = self._top_k_services(
            self._filter_profitable_services(
                self._normalize_services(services)
            ),
            problem
        )

        # ---- RL Optimization ----
        chromosome = self.optimizer.optimize(problem)
        services_selected = sum(chromosome.services)

        # ---- MILP ----
        clusters = self.split_by_hubs(problem)

        cluster_results = []

        for hub, ports in clusters.items():

            cluster_ids = {p.id for p in ports}

            cluster_demands = [
                d for d in problem.demands
                if d.origin in cluster_ids or d.destination in cluster_ids
            ]

            if not cluster_demands:
                continue

            sub_problem = Problem(
                ports=ports,
                services=problem.services,
                demands=cluster_demands,
                distance_matrix=problem.distance_matrix
            )

            result = HubMILP(sub_problem, chromosome).solve()
            cluster_results.append(result)

        total_profit = sum(r["profit"] for r in cluster_results)
        coverage = (
            sum(r["coverage"] for r in cluster_results) / len(cluster_results)
            if cluster_results else 0
        )
        operating_cost = sum(r.get("cost", 0) for r in cluster_results)

        # ---- Explanation ----
        explanation = self._generate_explanation(
            strategy,
            services_selected,
            total_profit,
            coverage
        )

        runtime = time.perf_counter() - start_time

        # ------------------------------------------------
        # SEND FEEDBACK TO ORCHESTRATOR
        # ------------------------------------------------

        feedback_payload = self._generate_feedback_payload(
            total_profit,
            coverage,
            services_selected
        )

        result = {
            "agent": self.name,
            "region": self.region,
            "status": "Optimal",

            "services_selected": services_selected,
            "weekly_profit": total_profit,
            "coverage_percent": coverage,
            "operating_cost": operating_cost,

            "strategy": strategy,
            "explanation": explanation,

            "feedback": feedback_payload,  # ✅ send feedback

            "meta": {
                "runtime_sec": round(runtime, 4)
            }
        }

        logger.info(
            "regional_agent_complete",
            region=self.region,
            profit=total_profit,
            coverage=coverage
        )

        return result

    # ------------------------------------------------
    # FEEDBACK HANDLING
    # ------------------------------------------------

    def _apply_feedback(self, problem, feedback):

        if not feedback:
            return problem

        logger.info("applying_feedback", feedback=feedback)

        if "low_coverage" in feedback:
            # Encourage broader coverage
            problem.demands = problem.demands + problem.demands[:10]

        if "underutilized_network" in feedback:
            # Allow more services
            problem.services = problem.services * 2

        if "negative_profit" in feedback:
            # Filter aggressively
            problem.services = [
                s for s in problem.services if s.capacity * 200 > s.weekly_cost
            ]

        return problem

    def _generate_feedback_payload(self, profit, coverage, services):

        issues = []

        if coverage < 60:
            issues.append("low_coverage")

        if profit < 0:
            issues.append("negative_profit")

        if services < 3:
            issues.append("underutilized_network")

        return {
            "issues": issues,
            "score": profit * 0.6 + coverage * 0.4
        }

    # ------------------------------------------------
    # HELPERS (UNCHANGED CORE)
    # ------------------------------------------------

    def _generate_strategy(self, problem, total_demand):
        try:
            return self.call_llm(
                f"Region: {self.region}, Demand: {total_demand}, Choose strategy",
                temperature=0.2
            )
        except:
            return "Hybrid strategy"

    def _normalize_services(self, services):
        normalized = []
        for i, s in enumerate(services):
            if isinstance(s, Service):
                normalized.append(s)
            else:
                normalized.append(
                    Service(
                        id=s.get("id", f"svc_{i}"),
                        ports=s["ports"],
                        capacity=s.get("capacity", 5000),
                        weekly_cost=s.get("weekly_cost", 800000),
                        cycle_time=s.get("cycle_time", 28)
                    )
                )
        return normalized

    def _filter_profitable_services(self, services):
        return [s for s in services if s.capacity * 150 > s.weekly_cost]

    def _top_k_services(self, services, problem):
        max_services = max(200, int(len(problem.ports) * 0.6))
        return sorted(
            services,
            key=lambda s: s.capacity / (s.weekly_cost + 1),
            reverse=True
        )[:max_services]

    def _generate_explanation(self, strategy, services, profit, coverage):
        try:
            return self.call_llm(
                f"Strategy: {strategy}, Profit: {profit}, Coverage: {coverage}",
                temperature=0.2
            )
        except:
            return "Stable solution"