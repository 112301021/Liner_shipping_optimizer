"""
Production-Grade Coordinator Agent (Decision Agent)
"""

from typing import Dict, Any, List
from src.agents.base import BaseAgent
from src.utils.config import Config
from src.utils.logger import logger


class CoordinatorAgent(BaseAgent):
    """
    Production Decision Agent

    Responsibilities:
    1. Detect conflicts
    2. Evaluate global performance
    3. Generate structured decisions
    4. Provide feedback signals (NOT just text)
    """

    def __init__(self, name: str = "coordinator", model: str = None):
        if model is None:
            model = Config.ORCHESTRATOR_MODEL

        super().__init__(
            name=name,
            role="Global Decision Agent",
            model=model
        )

    def get_system_prompt(self) -> str:
        return """You are a global shipping network decision agent.

You do NOT just summarize.
You ANALYZE, DECIDE, and CORRECT.

Focus on:
- Profit optimization
- Coverage balance
- Conflict resolution
- System efficiency

Return precise, actionable decisions."""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:

        regional_solutions = input_data['regional_solutions']

        logger.info("decision_agent_started",
                    num_regions=len(regional_solutions))

        # ---------------------------
        # 1. Conflict Detection
        # ---------------------------
        conflicts = self._identify_conflicts(regional_solutions)

        # ---------------------------
        # 2. Global Metrics
        # ---------------------------
        global_metrics = self._calculate_global_metrics(regional_solutions)

        # ---------------------------
        # 3. System Evaluation
        # ---------------------------
        evaluation = self._evaluate_system(global_metrics)

        # ---------------------------
        # 4. Decision Generation (LLM + Structure)
        # ---------------------------
        decisions = self._generate_decisions(
            conflicts,
            regional_solutions,
            global_metrics,
            evaluation
        )

        # ---------------------------
        # 5. Feedback Signals (IMPORTANT)
        # ---------------------------
        feedback = self._generate_feedback_signals(
            conflicts,
            global_metrics,
            evaluation
        )

        # ---------------------------
        # Final Output
        # ---------------------------
        result = {
            "agent": self.name,
            "status": "evaluated",

            "global_metrics": global_metrics,
            "evaluation": evaluation,

            "conflicts": conflicts,
            "decisions": decisions,      # structured LLM output
            "feedback": feedback        # machine-usable signals
        }

        logger.info("decision_agent_complete",
                    profit=global_metrics['total_profit'],
                    coverage=global_metrics['average_coverage'])

        return result

    # ============================================================
    # CONFLICT DETECTION
    # ============================================================
    def _identify_conflicts(self, regional_solutions: List[Dict]) -> List[Dict]:
        conflicts = []
        all_services = {}

        for solution in regional_solutions:
            region = solution['region']
            services = solution.get('chromosome', {}).get('services', [])

            for idx, selected in enumerate(services):
                if selected == 1:
                    if idx in all_services:
                        conflicts.append({
                            "type": "service_overlap",
                            "service_id": idx,
                            "regions": [all_services[idx], region]
                        })
                    else:
                        all_services[idx] = region

        return conflicts

    # ============================================================
    # GLOBAL METRICS
    # ============================================================
    def _calculate_global_metrics(self, regional_solutions: List[Dict]) -> Dict:

        total_services = sum(s['services_selected'] for s in regional_solutions)
        total_profit = sum(s['weekly_profit'] for s in regional_solutions)
        avg_coverage = sum(s['coverage_percent'] for s in regional_solutions) / len(regional_solutions)
        total_cost = sum(s['operating_cost'] for s in regional_solutions)

        return {
            "total_services": total_services,
            "total_profit": total_profit,
            "annual_profit": total_profit * 52,
            "average_coverage": avg_coverage,
            "total_cost": total_cost
        }

    # ============================================================
    # SYSTEM EVALUATION (NEW)
    # ============================================================
    def _evaluate_system(self, metrics: Dict) -> Dict:

        score = 0

        if metrics["average_coverage"] > 80:
            score += 1
        if metrics["total_profit"] > 0:
            score += 1
        if metrics["total_cost"] < metrics["total_profit"]:
            score += 1

        status = "good" if score >= 2 else "poor"

        return {
            "score": score,
            "status": status
        }

    # ============================================================
    # DECISION GENERATION (LLM)
    # ============================================================
    def _generate_decisions(self,
                           conflicts: List[Dict],
                           regional_solutions: List[Dict],
                           metrics: Dict,
                           evaluation: Dict) -> Dict:

        prompt = f"""
        Global Metrics:
        Profit: {metrics['total_profit']}
        Coverage: {metrics['average_coverage']}

        Evaluation: {evaluation['status']}

        Conflicts: {len(conflicts)}

        Provide structured decisions:
        1. Fix conflicts
        2. Improve weak regions
        3. Optimize cost vs coverage

        Output JSON:
        {{
            "actions": [],
            "priorities": [],
            "notes": ""
        }}
        """

        response = self.call_llm(prompt, temperature=0.3)

        return {"raw": response}

    # ============================================================
    # FEEDBACK SIGNALS (CRITICAL)
    # ============================================================
    def _generate_feedback_signals(self,
                                  conflicts: List[Dict],
                                  metrics: Dict,
                                  evaluation: Dict) -> Dict:

        return {
            "needs_rerun": (
                len(conflicts) > 0 or
                evaluation["status"] == "poor"
            ),
            "conflict_count": len(conflicts),
            "low_coverage": metrics["average_coverage"] < 70,
            "low_profit": metrics["total_profit"] <= 0
        }