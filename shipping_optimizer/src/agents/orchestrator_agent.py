"""
orchestrator_agent.py — Master Network Orchestrator
====================================================
Changes over the uploaded version:
  1. _apply_feedback: reads coordinator's weight_adjustments dict and applies
     them to the Problem object (profit_weight, coverage_weight, cost_weight)
     so the next GA pass actually uses different weights — not just bumps
     exploration_factor.
  2. process(): passes iteration counter to coordinator so feedback gradients
     respect the MAX_RERUN_ITERATIONS cap.
  3. Iteration audit trail: every loop iteration is logged with before/after
     metrics so you can see in logs exactly when feedback fired and what changed.
  4. decision_output included in final return for test assertions.
  5. summary_metrics contains 'cost' key required by existing test suite.
  6. status = 'complete' always set.
  7. aggregate_results: unchanged — uses true_global_demand as denominator.
"""

from __future__ import annotations

import re
import logging
from typing import Any, Dict, List

from src.llm.evaluator                   import LLMEvaluator
from src.agents.base                     import BaseAgent
from src.agents.regional_agent           import RegionalAgent
from src.decomposition.port_clustering   import PortClustering
from src.decomposition.regional_splitter import RegionalSplitter
from src.agents.coordinator_agent        import CoordinatorAgent
from src.optimization.data               import Problem
from src.utils.config                    import Config

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3   # hard ceiling — matches CoordinatorAgent.MAX_RERUN_ITERATIONS


class OrchestratorAgent(BaseAgent):

    def __init__(self, name: str = "orchestrator", model: str = None):
        if model is None:
            model = Config.ORCHESTRATOR_MODEL
        super().__init__(name=name, role="Master Orchestrator", model=model)
        self.evaluator = LLMEvaluator()
        self.regional_agents: List[RegionalAgent] = [
            RegionalAgent("regional_asia",     "Asia",     Config.REGIONAL_MODEL),
            RegionalAgent("regional_europe",   "Europe",   Config.REGIONAL_MODEL),
            RegionalAgent("regional_americas", "Americas", Config.REGIONAL_MODEL),
        ]
        self.coordinator = CoordinatorAgent()

        # ── Iteration audit trail ──────────────────────────────────────────
        # Each entry: {iteration, before_coverage, before_profit, after_coverage,
        #              after_profit, feedback_applied, weights_used}
        self.iteration_audit: List[Dict] = []

    def get_system_prompt(self) -> str:
        return (
            "You are the Master Orchestrator of a global liner shipping network "
            "optimization system built on a GA + MILP solver pipeline.\n\n"
            "Your output is used directly by a Decision Agent and reviewed by "
            "academic supervisors. Every claim MUST be grounded in the numeric "
            "data supplied. Do not generalise, hedge, or repeat the question. "
            "Produce concise, evidence-based analysis only."
        )

    # ================================================================
    # Validation helpers
    # ================================================================

    @staticmethod
    def _is_valid_analysis(text: str) -> bool:
        required = [
            "Size:", "Complexity Drivers:",
            "Demand Concentration:", "Decomposition Rationale:",
        ]
        return all(r in text for r in required) and any(c.isdigit() for c in text)

    @staticmethod
    def _is_valid_summary(text: str) -> bool:
        required = ["Verdict:", "Strength", "Weakness", "Priority"]
        return all(r in text for r in required) and bool(re.search(r"\d{2,}", text))

    # ================================================================
    # Problem analysis (unchanged from uploaded version)
    # ================================================================

    def analyze_problem(self, problem: Problem) -> str:
        total_demand  = sum(d.weekly_teu for d in problem.demands)
        num_ports     = len(problem.ports)
        num_services  = len(problem.services)
        num_lanes     = len(problem.demands)
        avg_demand    = total_demand / num_lanes if num_lanes else 0
        density_ratio = round(
            num_lanes / (num_ports * (num_ports - 1) / 2) * 100, 1
        ) if num_ports > 1 else 0

        top5       = sorted(problem.demands, key=lambda d: d.weekly_teu, reverse=True)[:5]
        top5_teu   = sum(d.weekly_teu for d in top5)
        top5_share = round(top5_teu / total_demand * 100, 1) if total_demand else 0

        top5_text = "\n".join(
            f"  {i+1}. Port {d.origin} -> Port {d.destination}: {d.weekly_teu:,.0f} TEU/week"
            for i, d in enumerate(top5)
        )
        size_label = "Small" if num_ports < 50 else ("Medium" if num_ports <= 200 else "Large")

        prompt = (
            f"Network statistics (ground truth):\n"
            f"  Ports: {num_ports}, Lanes: {num_lanes}, Services: {num_services}\n"
            f"  Total demand: {total_demand:,.0f} TEU/wk, Avg/lane: {avg_demand:,.1f} TEU\n"
            f"  Density: {density_ratio}%, Top-5 share: {top5_share}%\n\n"
            f"TOP-5 CORRIDORS:\n{top5_text}\n\n"
            f"STRICT FORMAT:\n"
            f"Size: {size_label}\n"
            f"Complexity Drivers:\n"
            f"- [Driver 1 with specific statistic]\n"
            f"- [Driver 2 with specific statistic]\n"
            f"- [Driver 3 with specific statistic]\n"
            f"Demand Concentration: [high/moderate/low] - [one sentence implication]\n"
            f"Decomposition Rationale: [one sentence with ~{num_ports//3} ports per region]"
        )

        try:
            analysis = ""
            for _ in range(2):
                analysis = self.call_llm(prompt, temperature=0.1)
                if self._is_valid_analysis(analysis):
                    break
        except Exception:
            analysis = ""

        if not self._is_valid_analysis(analysis):
            conc = (
                "high" if top5_share > 40 else
                "moderate" if top5_share > 20 else "low"
            )
            analysis = (
                f"Size: {size_label}\n"
                f"Complexity Drivers:\n"
                f"- {num_ports} ports x {num_lanes} lanes -> combinatorial explosion "
                f"above {num_ports**2} route candidates.\n"
                f"- Network density {density_ratio}% across {num_ports} ports "
                f"increases routing difficulty.\n"
                f"- Total demand {total_demand:,.0f} TEU requires capacity balancing "
                f"across {num_services} services.\n"
                f"Demand Concentration: {conc} - top-5 share {top5_share}% implies "
                f"{'hub selection is critical.' if top5_share > 40 else 'mixed hub and direct strategy.'}\n"
                f"Decomposition Rationale: ~{num_ports // 3} ports per region enables "
                f"scalable 3-agent optimization."
            )
        return analysis

    # ================================================================
    # Aggregate results (unchanged — true_global_demand denominator)
    # ================================================================

    def aggregate_results(
        self,
        regional_results: List[Dict],
        true_global_demand: float,
    ) -> Dict:
        total_profit    = 0.0
        total_operating = 0.0
        total_transship = 0.0
        total_port_cost = 0.0
        total_cost      = 0.0
        total_services  = 0
        total_satisfied = 0.0
        total_unserved  = 0.0

        for r in regional_results:
            total_profit    += r.get("weekly_profit",    0.0)
            total_operating += r.get("operating_cost",   0.0)
            total_transship += r.get("transship_cost",   0.0)
            total_port_cost += r.get("port_cost",        0.0)
            total_cost      += r.get("total_cost",       0.0)
            total_services  += r.get("services_selected", 0)
            total_satisfied += r.get("satisfied_demand",  0.0)
            total_unserved  += r.get("unserved_demand",   0.0)

        # Cap satisfied at true global demand
        total_satisfied = min(total_satisfied, true_global_demand)
        coverage = (
            total_satisfied / true_global_demand * 100
            if true_global_demand > 0 else 0.0
        )

        return {
            "weekly_profit":   total_profit,
            "annual_profit":   total_profit * 52,
            "operating_cost":  total_operating,
            "transship_cost":  total_transship,
            "port_cost":       total_port_cost,
            "total_cost":      total_cost,
            "cost":            total_cost,           # alias for test suite
            "total_services":  total_services,
            "satisfied_demand": total_satisfied,
            "unserved_demand": total_unserved,
            "coverage":        coverage,
        }

    # ================================================================
    # Feedback application — THE KEY FIX
    # ================================================================

    def _apply_feedback(self, problem: Problem, decision_output: Dict) -> Problem:
        """
        Apply coordinator's gradient feedback to the Problem object so the
        next GA pass uses different weights.

        Priority order:
          1. decision_output["decisions"]["weight_adjustments"]  (LLM-derived)
          2. decision_output["feedback"]["weight_adjustments"]   (gradient-derived)
          3. Simple heuristic based on coverage_gap
        """
        feedback  = decision_output.get("feedback", {})
        decisions = decision_output.get("decisions", {})

        # ── Get weight adjustments ─────────────────────────────────────────
        weights = (
            decisions.get("weight_adjustments") or
            feedback.get("weight_adjustments") or
            {}
        )

        if not weights:
            # Last-resort heuristic
            cov_gap   = feedback.get("coverage_gap", 0.0)
            cov_boost = min(0.20, cov_gap / 100.0)
            weights = {
                "profit_weight":   max(0.30, 0.50 - cov_boost),
                "coverage_weight": min(0.60, 0.40 + cov_boost),
                "cost_weight":     0.10,
            }

        # ── Apply to Problem ───────────────────────────────────────────────
        before = {
            "profit_weight":   getattr(problem, "profit_weight",   0.5),
            "coverage_weight": getattr(problem, "coverage_weight", 0.4),
            "cost_weight":     getattr(problem, "cost_weight",     0.1),
        }

        problem.profit_weight   = weights.get("profit_weight",   before["profit_weight"])
        problem.coverage_weight = weights.get("coverage_weight", before["coverage_weight"])
        problem.cost_weight     = weights.get("cost_weight",     before["cost_weight"])

        # Still bump exploration factor for diversity
        problem.exploration_factor = getattr(problem, "exploration_factor", 1.0) * 1.1

        logger.info(
            "feedback_applied",
            before_weights=before,
            after_weights={
                "profit_weight":   problem.profit_weight,
                "coverage_weight": problem.coverage_weight,
                "cost_weight":     problem.cost_weight,
            },
            coverage_gap=feedback.get("coverage_gap", 0),
            conflict_severity=feedback.get("conflict_severity", 0),
        )

        return problem

    # ================================================================
    # Main process
    # ================================================================

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("orchestrator_started")
        problem: Problem = input_data["problem"]

        # Capture TRUE global demand BEFORE splitting
        true_global_demand = sum(d.weekly_teu for d in problem.demands)
        logger.info("true_global_demand_captured", teu=true_global_demand)

        analysis = self.analyze_problem(problem)
        logger.info("problem_analysis_complete")

        # Decompose
        clustering = PortClustering(n_clusters=len(self.regional_agents))
        clusters   = clustering.cluster_ports(problem.ports)

        # ── Feedback / resolution loop ─────────────────────────────────────
        regional_results: List[Dict] = []
        decision_output:  Dict       = {}
        prev_coverage: float         = -1.0   # FIX 5: track previous iteration coverage

        for iteration in range(MAX_ITERATIONS):
            logger.info("iteration_start", iteration=iteration)

            # Snapshot weights before this iteration
            weights_before = {
                "profit_weight":   getattr(problem, "profit_weight",   0.5),
                "coverage_weight": getattr(problem, "coverage_weight", 0.4),
                "cost_weight":     getattr(problem, "cost_weight",     0.1),
            }

            splitter          = RegionalSplitter(problem)
            regional_problems = splitter.split(clusters)
            regional_results  = []

            for i, agent in enumerate(self.regional_agents):
                rp = regional_problems.get(i)
                if rp is None:
                    continue
                result = agent.process({"problem": rp})
                regional_results.append(result)

            # Snapshot metrics after this iteration
            iter_profit   = sum(r.get("weekly_profit", 0) for r in regional_results)
            iter_coverage = (
                sum(r.get("coverage_percent", 0) for r in regional_results) /
                len(regional_results)
            ) if regional_results else 0.0

            # Coordinator with iteration counter for cap enforcement
            decision_output = self.coordinator.process({
                "regional_solutions": regional_results,
                "problem":            problem,
                "iteration":          iteration,
            })

            feedback  = decision_output["feedback"]
            decisions = decision_output["decisions"]

            logger.info(
                "iteration_complete",
                iteration=iteration,
                profit=f"${iter_profit:,.0f}",
                coverage=f"{iter_coverage:.1f}%",
                convergence_score=feedback["convergence_score"],
                needs_rerun=feedback["needs_rerun"],
                rerun_reason=feedback["rerun_reason"],
            )

            # ── Record audit entry ─────────────────────────────────────────
            self.iteration_audit.append({
                "iteration":          iteration,
                "weights_used":       weights_before,
                "profit":             iter_profit,
                "coverage":           iter_coverage,
                "convergence_score":  feedback["convergence_score"],
                "coverage_gap":       feedback["coverage_gap"],
                "conflict_severity":  feedback["conflict_severity"],
                "needs_rerun":        feedback["needs_rerun"],
                "rerun_reason":       feedback["rerun_reason"],
                "resolution_log":     decision_output.get("resolution_log", []),
            })

            # ── STOP CONDITION ─────────────────────────────────────────────
            if not feedback["needs_rerun"]:
                logger.info(
                    "pipeline_converged",
                    iteration=iteration,
                    coverage=f"{iter_coverage:.1f}%",
                    convergence_score=feedback["convergence_score"],
                )
                break

            # FIX 5: Early stop if coverage improvement < 1% between iterations
            if prev_coverage >= 0 and (iter_coverage - prev_coverage) < 1.0:
                logger.info(
                    "pipeline_early_stop_no_coverage_gain",
                    iteration=iteration,
                    prev_coverage=f"{prev_coverage:.1f}%",
                    curr_coverage=f"{iter_coverage:.1f}%",
                )
                break
            prev_coverage = iter_coverage

            # ── APPLY FEEDBACK for next iteration ─────────────────────────
            problem = self._apply_feedback(problem, decision_output)

        # ── Final aggregation ──────────────────────────────────────────────
        metrics = self.aggregate_results(regional_results, true_global_demand)

        weekly_profit  = metrics["weekly_profit"]
        annual_profit  = metrics["annual_profit"]
        total_cost     = metrics["total_cost"]
        operating_cost = metrics["operating_cost"]
        transship_cost = metrics["transship_cost"]
        port_cost      = metrics["port_cost"]
        coverage       = metrics["coverage"]
        total_services = metrics["total_services"]
        unserved_teu   = metrics["unserved_demand"]

        profit_margin_pct  = round(
            weekly_profit / (weekly_profit + total_cost) * 100, 1
        ) if (weekly_profit + total_cost) > 0 else 0
        cost_per_service   = round(total_cost   / total_services, 0) if total_services else 0
        profit_per_service = round(weekly_profit / total_services, 0) if total_services else 0
        uncovered_pct      = round(100 - coverage, 1)

        region_lines = "\n".join(
            f"  {r['region']:12s}: profit=${r['weekly_profit']:>12,.0f}/wk  "
            f"coverage={r['coverage_percent']:>5.1f}%  "
            f"services={r['services_selected']:>4d}  "
            f"op_cost=${r['operating_cost']:>10,.0f}  "
            f"transship=${r.get('transship_cost', 0):>8,.0f}  "
            f"port=${r.get('port_cost', 0):>8,.0f}"
            for r in regional_results if "region" in r
        )

        top_demands = sorted(problem.demands, key=lambda d: d.weekly_teu, reverse=True)[:5]
        top5_text   = "\n".join(
            f"  {i+1}. Port {d.origin} -> Port {d.destination}: {d.weekly_teu:,.0f} TEU/week"
            for i, d in enumerate(top_demands)
        )

        summary_prompt = (
            f"Senior maritime analyst reviewing GA + MILP optimized network.\n\n"
            f"GLOBAL RESULTS (solver ground truth):\n"
            f"  Services deployed    : {total_services}\n"
            f"  Weekly profit        : ${weekly_profit:,.0f}    | Annual: ${annual_profit:,.0f}\n"
            f"  Profit margin        : {profit_margin_pct}%\n"
            f"  Cost breakdown       : Operating ${operating_cost:,.0f} | "
            f"Transship ${transship_cost:,.0f} | Port ${port_cost:,.0f}\n"
            f"  Profit/service       : ${profit_per_service:,.0f}/wk | "
            f"Cost/service: ${cost_per_service:,.0f}/wk\n"
            f"  Demand coverage      : {coverage:.1f}%   | "
            f"Unserved: {uncovered_pct:.1f}% ({unserved_teu:,.0f} TEU/wk)\n\n"
            f"REGIONAL BREAKDOWN:\n{region_lines}\n\n"
            f"TOP-5 GLOBAL CORRIDORS:\n{top5_text}\n\n"
            f"STRICT FORMAT - no hedging language:\n"
            f"Verdict: <Good | Moderate | Poor>\n"
            f"  [One sentence: cite profit margin {profit_margin_pct}% and coverage {coverage:.1f}%]\n\n"
            f"Strengths:\n"
            f"- [Cite weekly profit ${weekly_profit:,.0f} and per-service efficiency]\n"
            f"- [Cite transship + port cost breakdown relative to operating cost]\n\n"
            f"Weaknesses:\n"
            f"- [Cite unserved {uncovered_pct:.1f}% = {unserved_teu:,.0f} TEU/wk revenue loss]\n"
            f"- [Cite cost/service ${cost_per_service:,.0f} sustainability concern]\n\n"
            f"Priority Actions:\n"
            f"- [Name lowest-coverage region with its coverage % and service count target]\n"
            f"- [Name top unserved corridor (port IDs + TEU) and specific remediation]"
        )

        try:
            executive_summary = ""
            for _ in range(2):
                executive_summary = self.call_llm(summary_prompt, temperature=0.1)
                if self._is_valid_summary(executive_summary):
                    break
        except Exception:
            executive_summary = ""

        if not self._is_valid_summary(executive_summary):
            lowest = min(
                (r for r in regional_results if "region" in r),
                key=lambda r: r.get("coverage_percent", 100),
                default={},
            )
            executive_summary = (
                f"Verdict: {'Good' if profit_margin_pct > 60 else 'Moderate' if profit_margin_pct > 30 else 'Poor'}\n"
                f"  Profit margin {profit_margin_pct}% with {coverage:.1f}% demand coverage.\n\n"
                f"Strengths:\n"
                f"- Weekly profit ${weekly_profit:,.0f} across {total_services} services "
                f"(${profit_per_service:,.0f}/service/week).\n"
                f"- Cost breakdown: operating ${operating_cost:,.0f}, transship "
                f"${transship_cost:,.0f}, port ${port_cost:,.0f}/week.\n\n"
                f"Weaknesses:\n"
                f"- {uncovered_pct:.1f}% demand ({unserved_teu:,.0f} TEU/week) unserved.\n"
                f"- Cost per service ${cost_per_service:,.0f}/week limits expansion.\n\n"
                f"Priority Actions:\n"
                f"- Expand {lowest.get('region', 'lowest-coverage region')} "
                f"(currently {lowest.get('coverage_percent', 0):.1f}% coverage).\n"
                f"- Route capacity to Port {top_demands[0].origin} -> Port "
                f"{top_demands[0].destination} ({top_demands[0].weekly_teu:,.0f} TEU/week)."
            )

        logger.info("orchestrator_complete")

        return {
            "orchestrator":      self.name,
            "status":            "complete",
            "problem_analysis":  analysis,
            "regional_results":  regional_results,
            "decision_output":   decision_output,
            "executive_summary": executive_summary,
            "summary_metrics":   metrics,
            "iteration_audit":   self.iteration_audit,   # ← NEW: full loop history
            "iterations_run":    len(self.iteration_audit),
        }