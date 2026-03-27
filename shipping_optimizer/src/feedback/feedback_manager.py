from typing import Dict, List
from src.utils.logger import logger


class FeedbackManager:
    """
    Central feedback aggregation + decision logic

    Handles:
    - Collect feedback from agents
    - Detect global issues
    - Trigger resolution loops
    - Future: RL training data storage
    """

    def __init__(self):

        self.history = []

    # ------------------------------------------------
    def collect(self, regional_results: List[Dict]):

        feedback_data = []

        for r in regional_results:

            fb = r.get("feedback", {})

            feedback_data.append({
                "agent": r.get("agent"),
                "region": r.get("region"),
                "issues": fb.get("issues", []),
                "score": fb.get("score", 0)
            })

        self.history.append(feedback_data)

        logger.info("feedback_collected", count=len(feedback_data))

        return feedback_data

    # ------------------------------------------------
    def analyze(self, feedback_data: List[Dict]):

        global_issues = {}

        for fb in feedback_data:
            for issue in fb["issues"]:
                global_issues[issue] = global_issues.get(issue, 0) + 1

        logger.info("feedback_analyzed", issues=global_issues)

        return global_issues

    # ------------------------------------------------
    def should_trigger_resolution(self, issues: Dict) -> bool:

        # Trigger if major issues exist
        critical = ["low_coverage", "negative_profit"]

        for c in critical:
            if issues.get(c, 0) > 0:
                return True

        return False

    # ------------------------------------------------
    def build_resolution_payload(self, issues: Dict):

        # Convert global issues into actionable feedback
        payload = []

        for issue, count in issues.items():
            if count > 0:
                payload.append(issue)

        logger.info("resolution_payload_created", payload=payload)

        return payload

    # ------------------------------------------------
    def log_iteration(self, iteration, metrics):

        logger.info(
            "feedback_iteration",
            iteration=iteration,
            metrics=metrics
        )