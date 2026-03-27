from typing import Dict, Any, List
import time

from src.agents.base import BaseAgent
from src.agents.regional_agent import RegionalAgent
from src.decomposition.port_clustering import PortClustering
from src.decomposition.regional_splitter import RegionalSplitter
from src.feedback.feedback_manager import FeedbackManager
from src.optimization.data import Problem
from src.utils.config import Config
from src.utils.logger import logger


class OrchestratorAgent(BaseAgent):

    def __init__(self, name: str = "orchestrator", model: str = None, rl_model_path: str = None):

        if model is None:
            model = Config.ORCHESTRATOR_MODEL

        super().__init__(
            name=name,
            role="Master Orchestrator",
            model=model
        )
        self.feedback_manager = FeedbackManager()

        # RL-enabled regional agents
        self.regional_agents = [
            RegionalAgent("regional_asia", "Asia", Config.REGIONAL_MODEL, rl_model_path),
            RegionalAgent("regional_europe", "Europe", Config.REGIONAL_MODEL, rl_model_path),
            RegionalAgent("regional_americas", "Americas", Config.REGIONAL_MODEL, rl_model_path)
        ]

    # ------------------------------------------------
    def get_system_prompt(self) -> str:
        return """
You are the Master Orchestrator of a global shipping optimization system.

Responsibilities:
- Decompose problems
- Coordinate agents
- Evaluate system performance
- Trigger refinements

Focus on adaptive, feedback-driven optimization.
"""

    # ------------------------------------------------
    def analyze_problem(self, problem: Problem) -> str:

        total_demand = sum(d.weekly_teu for d in problem.demands)

        try:
            analysis = self.call_llm(f"""
Ports: {len(problem.ports)}
Demand: {total_demand}

Classify problem + challenges.
""", temperature=0.3)

            return analysis
        except:
            return "Analysis unavailable"

    # ------------------------------------------------
    # CORE: FEEDBACK LOOP
    # ------------------------------------------------
    def _evaluate_and_feedback(self, regional_results):

        feedback = []

        for r in regional_results:

            score = (
                r.get("weekly_profit", 0) * 0.6 +
                r.get("coverage_percent", 0) * 0.4
            )

            feedback.append({
                "agent": r["agent"],
                "score": score,
                "issues": self._detect_issues(r)
            })

        return feedback

    def _detect_issues(self, result):

        issues = []

        if result.get("coverage_percent", 0) < 60:
            issues.append("low_coverage")

        if result.get("weekly_profit", 0) < 0:
            issues.append("negative_profit")

        if result.get("services_selected", 0) < 3:
            issues.append("underutilized_network")

        return issues

    # ------------------------------------------------
    # RESOLUTION LOOP (CRITICAL)
    # ------------------------------------------------
    def _resolution_loop(self, regional_problems, max_iters=2):

        final_results = []

        for idx, agent in enumerate(self.regional_agents):

            problem = regional_problems.get(idx)
            if problem is None:
                continue

            result = agent.process({"problem": problem})

            for _ in range(max_iters):

                issues = self._detect_issues(result)

                if not issues:
                    break

                logger.info(
                    "resolution_triggered",
                    agent=agent.name,
                    issues=issues
                )

                # Adjust problem heuristically
                problem = self._adjust_problem(problem, issues)

                result = agent.process({
                    "problem": problem,
                    "feedback": issues
                })

            final_results.append(result)

        return final_results

    def _adjust_problem(self, problem, issues):

        # Lightweight adaptive modification (RL-friendly)

        if "low_coverage" in issues:
            problem.demands = problem.demands[:int(len(problem.demands) * 1.2)]

        if "underutilized_network" in issues:
            problem.services = problem.services[:int(len(problem.services) * 1.3)]

        return problem

    # ------------------------------------------------
    def aggregate_results(self, regional_results):

        total_services = sum(r.get("services_selected", 0) for r in regional_results)
        total_profit = sum(r.get("weekly_profit", 0) for r in regional_results)
        total_cost = sum(r.get("operating_cost", 0) for r in regional_results)

        avg_coverage = (
            sum(r.get("coverage_percent", 0) for r in regional_results) / len(regional_results)
            if regional_results else 0
        )

        return {
            "total_services": total_services,
            "weekly_profit": total_profit,
            "annual_profit": total_profit * 52,
            "coverage": avg_coverage,
            "cost": total_cost
        }

    # ------------------------------------------------
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:

        start_time = time.time()

        logger.info("orchestrator_started")

        problem: Problem = input_data["problem"]

        # ---- Step 1: Analysis ----
        analysis = self.analyze_problem(problem)

        # ---- Step 2: Decomposition ----
        clustering = PortClustering(n_clusters=len(self.regional_agents))
        clusters = clustering.cluster_ports(problem.ports)

        splitter = RegionalSplitter(problem)
        regional_problems = splitter.split(clusters)

        # ---- Step 3: RL + Resolution Loop ----
        regional_results = self._resolution_loop(regional_problems)

        # ---- Step 4: Feedback Aggregation ----
        feedback_data = self.feedback_manager.collect(regional_results)

        issues = self.feedback_manager.analyze(feedback_data)

        # -----------------------------
        # STEP: Resolution Loop (if needed)
        # -----------------------------
        if self.feedback_manager.should_trigger_resolution(issues):

            payload = self.feedback_manager.build_resolution_payload(issues)

            logger.info("resolution_triggered", issues=payload)

            updated_results = []

            for idx, agent in enumerate(self.regional_agents):

                regional_problem = regional_problems.get(idx)

                if regional_problem is None:
                    continue

                result = agent.process({
                    "problem": regional_problem,
                    "feedback": payload   # ✅ SEND FEEDBACK
                })

                updated_results.append(result)

            regional_results = updated_results

        # ---- Step 5: Metrics ----
        metrics = self.aggregate_results(regional_results)

        # ---- Step 6: Executive Summary ----
        summary = self._generate_summary(metrics)

        latency = time.time() - start_time

        logger.info(
            "orchestrator_complete",
            profit=metrics["weekly_profit"],
            latency=latency
        )

        return {
            "orchestrator": self.name,
            "status": "complete",

            "problem_analysis": analysis,
            "regional_results": regional_results,
            "feedback": feedback_data,

            "summary_metrics": metrics,
            "executive_summary": summary,

            "meta": {
                "latency_sec": round(latency, 4)
            }
        }

    # ------------------------------------------------
    def _generate_summary(self, metrics):

        try:
            return self.call_llm(f"""
Services: {metrics['total_services']}
Profit: {metrics['weekly_profit']}
Coverage: {metrics['coverage']}

Evaluate network.
""", temperature=0.2)

        except:
            return "Summary unavailable"