"""
coordinator_agent.py — Production Coordinator / Decision Agent
==============================================================
Fixes over the uploaded version:
  1. _identify_conflicts: handles chromosome["services"] as EITHER a binary
     list OR a list of service-id strings (both formats used in the codebase).
  2. _generate_decisions: extracts structured JSON from LLM properly and
     falls back to a rule-based decision tree — no more {"raw": text}.
  3. _generate_feedback_signals: returns GRADIENT signals (floats), not just
     binary flags, so the orchestrator knows HOW MUCH to adjust.
  4. _resolve_conflicts: new method — applies concrete per-conflict fix
     (drop the service from the lower-profit region's chromosome).
  5. Full iteration audit trail: every rerun reason is logged with numbers.
  6. "needs_rerun" is False only when both coverage and conflict thresholds
     are met — prevents premature convergence AND infinite loops.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from src.agents.base   import BaseAgent
from src.utils.config  import Config
from src.utils.logger  import logger


# ── Thresholds (tunable) ─────────────────────────────────────────────────
COVERAGE_TARGET        = 70.0   # % — below this a rerun is triggered
PROFIT_FLOOR           = 0.0    # weekly USD — negative profit triggers rerun
MAX_CONFLICTS_ALLOWED  = 0      # any overlap triggers resolution pass
MAX_RERUN_ITERATIONS   = 3      # hard cap passed in from orchestrator


class CoordinatorAgent(BaseAgent):
    """
    Global Decision Agent — coordinates regional results, resolves conflicts,
    and emits machine-usable feedback gradients for the orchestrator.
    """

    def __init__(self, name: str = "coordinator", model: str = None):
        super().__init__(
            name=name,
            role="Global Decision Agent",
            model=model or Config.ORCHESTRATOR_MODEL,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are a global shipping network decision agent.\n\n"
            "You ANALYZE, DECIDE, and CORRECT — not summarise.\n\n"
            "Rules:\n"
            "- Every decision must cite a specific number.\n"
            "- Actions must be concrete and measurable.\n"
            "- Output valid JSON only when requested.\n"
            "- No hedging language."
        )

    # ================================================================
    # PUBLIC ENTRY POINT
    # ================================================================

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        regional_solutions: List[Dict] = input_data["regional_solutions"]
        iteration: int                 = input_data.get("iteration", 0)

        logger.info(
            "coordinator_started",
            num_regions=len(regional_solutions),
            iteration=iteration,
        )

        # 1. Conflict detection
        conflicts = self._identify_conflicts(regional_solutions)

        # 2. Conflict resolution (mutates chromosomes in-place)
        resolution_log = self._resolve_conflicts(conflicts, regional_solutions)

        # 3. Global metrics
        global_metrics = self._calculate_global_metrics(regional_solutions)

        # 4. System evaluation
        evaluation = self._evaluate_system(global_metrics, conflicts)

        # 5. Structured LLM decisions
        decisions = self._generate_decisions(
            conflicts, regional_solutions, global_metrics, evaluation
        )

        # 6. Machine-usable feedback gradients
        feedback = self._generate_feedback_signals(
            conflicts, global_metrics, evaluation, iteration
        )

        logger.info(
            "coordinator_complete",
            profit=global_metrics["total_profit"],
            coverage=global_metrics["average_coverage"],
            conflicts=len(conflicts),
            needs_rerun=feedback["needs_rerun"],
            rerun_reason=feedback["rerun_reason"],
        )

        return {
            "agent":           self.name,
            "iteration":       iteration,
            "status":          "evaluated",
            "global_metrics":  global_metrics,
            "evaluation":      evaluation,
            "conflicts":       conflicts,
            "resolution_log":  resolution_log,
            "decisions":       decisions,
            "feedback":        feedback,
        }

    # ================================================================
    # 1. CONFLICT DETECTION
    # ================================================================

    def _identify_conflicts(self, regional_solutions: List[Dict]) -> List[Dict]:
        """
        Detect services deployed in more than one region.

        Handles two chromosome formats:
          A) binary list  [0, 1, 0, 1, ...]  (index = service position)
          B) id list      ["SVC_001", "SVC_042", ...]
        """
        conflicts: List[Dict] = []
        service_to_regions: Dict[Any, List[str]] = {}

        for solution in regional_solutions:
            region   = solution.get("region", "unknown")
            chrom    = solution.get("chromosome", {})
            services = chrom.get("services", [])

            if not services:
                continue

            # Detect format
            if isinstance(services[0], int):
                # Format A: binary list
                selected_ids = [
                    i for i, flag in enumerate(services) if flag == 1
                ]
            else:
                # Format B: explicit id list
                selected_ids = list(services)

            for sid in selected_ids:
                if sid not in service_to_regions:
                    service_to_regions[sid] = []
                service_to_regions[sid].append(region)

        for sid, regions in service_to_regions.items():
            if len(regions) > 1:
                conflicts.append({
                    "type":       "service_overlap",
                    "service_id": sid,
                    "regions":    regions,
                })

        logger.info("conflicts_detected", count=len(conflicts))
        return conflicts

    # ================================================================
    # 2. CONFLICT RESOLUTION
    # ================================================================

    def _resolve_conflicts(
        self,
        conflicts: List[Dict],
        regional_solutions: List[Dict],
    ) -> List[Dict]:
        """
        For each overlap, drop the service from the LOWER-profit region.
        Mutates chromosome in the regional_solutions list (used in next GA pass).
        Returns an audit log entry per conflict resolved.
        """
        if not conflicts:
            return []

        # Index solutions by region for O(1) lookup
        by_region = {s["region"]: s for s in regional_solutions}
        resolution_log: List[Dict] = []

        for conflict in conflicts:
            sid     = conflict["service_id"]
            regions = conflict["regions"]

            # Sort by profit — keep in highest-profit region
            sorted_regions = sorted(
                regions,
                key=lambda r: by_region.get(r, {}).get("weekly_profit", 0),
                reverse=True,
            )
            keep_region = sorted_regions[0]
            drop_regions = sorted_regions[1:]

            for drop_r in drop_regions:
                sol   = by_region.get(drop_r)
                if not sol:
                    continue
                chrom = sol.get("chromosome", {})
                svcs  = chrom.get("services", [])

                if not svcs:
                    continue

                if isinstance(svcs[0], int):
                    # Binary format: zero out the flag
                    if isinstance(sid, int) and sid < len(svcs):
                        svcs[sid] = 0
                else:
                    # ID format: remove the id
                    if sid in svcs:
                        svcs.remove(sid)

                resolution_log.append({
                    "service_id":    sid,
                    "kept_in":       keep_region,
                    "removed_from":  drop_r,
                    "keep_profit":   by_region.get(keep_region, {}).get("weekly_profit", 0),
                    "drop_profit":   sol.get("weekly_profit", 0),
                })

        logger.info("conflicts_resolved", resolved=len(resolution_log))
        return resolution_log

    # ================================================================
    # 3. GLOBAL METRICS
    # ================================================================

    def _calculate_global_metrics(self, regional_solutions: List[Dict]) -> Dict:
        if not regional_solutions:
            return {
                "total_services": 0, "total_profit": 0.0, "annual_profit": 0.0,
                "average_coverage": 0.0, "min_coverage": 0.0,
                "max_coverage": 0.0, "total_cost": 0.0,
                "total_satisfied_demand": 0.0, "total_unserved_demand": 0.0,
            }

        coverages        = [s.get("coverage_percent", 0.0) for s in regional_solutions]
        total_profit     = sum(s.get("weekly_profit", 0.0)        for s in regional_solutions)
        total_cost       = sum(s.get("operating_cost", 0.0)       for s in regional_solutions)
        total_satisfied  = sum(s.get("satisfied_demand", 0.0)     for s in regional_solutions)
        total_unserved   = sum(s.get("unserved_demand", 0.0)      for s in regional_solutions)
        total_services   = sum(s.get("services_selected", 0)      for s in regional_solutions)

        return {
            "total_services":          total_services,
            "total_profit":            total_profit,
            "annual_profit":           total_profit * 52,
            "average_coverage":        sum(coverages) / len(coverages),
            "min_coverage":            min(coverages),
            "max_coverage":            max(coverages),
            "coverage_variance":       max(coverages) - min(coverages),
            "total_cost":              total_cost,
            "total_satisfied_demand":  total_satisfied,
            "total_unserved_demand":   total_unserved,
            "profit_margin_pct": round(
                total_profit / (total_profit + total_cost) * 100, 1
            ) if (total_profit + total_cost) > 0 else 0.0,
        }

    # ================================================================
    # 4. SYSTEM EVALUATION
    # ================================================================

    def _evaluate_system(self, metrics: Dict, conflicts: List[Dict]) -> Dict:
        score   = 0
        reasons = []

        if metrics["average_coverage"] >= COVERAGE_TARGET:
            score += 1
        else:
            reasons.append(
                f"coverage {metrics['average_coverage']:.1f}% < target {COVERAGE_TARGET}%"
            )

        if metrics["total_profit"] > PROFIT_FLOOR:
            score += 1
        else:
            reasons.append(f"profit ${metrics['total_profit']:,.0f} <= floor ${PROFIT_FLOOR:,.0f}")

        if metrics["total_cost"] < metrics["total_profit"]:
            score += 1
        else:
            reasons.append("cost exceeds profit")

        if len(conflicts) <= MAX_CONFLICTS_ALLOWED:
            score += 1
        else:
            reasons.append(f"{len(conflicts)} service overlap conflicts detected")

        if metrics["coverage_variance"] <= 20.0:
            score += 1
        else:
            reasons.append(
                f"coverage variance {metrics['coverage_variance']:.1f}% — "
                "regions imbalanced"
            )

        status = (
            "good"     if score >= 4 else
            "moderate" if score >= 2 else
            "poor"
        )

        return {
            "score":   score,
            "max":     5,
            "status":  status,
            "reasons": reasons,
        }

    # ================================================================
    # 5. STRUCTURED LLM DECISIONS
    # ================================================================

    def _generate_decisions(
        self,
        conflicts:           List[Dict],
        regional_solutions:  List[Dict],
        metrics:             Dict,
        evaluation:          Dict,
    ) -> Dict:
        """
        Returns a structured dict with 'actions' and 'priorities'.
        LLM output is parsed as JSON; falls back to rule-based decisions
        so the orchestrator always gets machine-usable data.
        """
        weak_regions = [
            s for s in regional_solutions
            if s.get("coverage_percent", 0) < COVERAGE_TARGET
        ]
        weak_summary = "; ".join(
            f"{s['region']} coverage={s.get('coverage_percent', 0):.1f}%"
            for s in weak_regions
        )

        prompt = f"""
Global shipping network decision — iteration results:

Metrics:
  Total profit   : ${metrics['total_profit']:,.0f}/week
  Annual profit  : ${metrics['annual_profit']:,.0f}
  Avg coverage   : {metrics['average_coverage']:.1f}%
  Min coverage   : {metrics['min_coverage']:.1f}%
  Coverage variance: {metrics['coverage_variance']:.1f}%
  Total cost     : ${metrics['total_cost']:,.0f}/week
  Profit margin  : {metrics['profit_margin_pct']:.1f}%
  Evaluation     : {evaluation['status']} (score {evaluation['score']}/{evaluation['max']})

Conflicts detected: {len(conflicts)}
Weak regions (coverage < {COVERAGE_TARGET}%): {weak_summary or 'none'}

Return ONLY valid JSON (no markdown, no preamble):
{{
  "actions": [
    {{"region": "<name>", "action": "<verb> <object>", "expected_gain": "<metric change>"}}
  ],
  "priorities": ["<priority 1>", "<priority 2>"],
  "weight_adjustments": {{
    "profit_weight":   <0.0-1.0>,
    "coverage_weight": <0.0-1.0>,
    "cost_weight":     <0.0-1.0>
  }},
  "notes": "<one sentence with specific numbers>"
}}
"""
        raw = self.call_llm(prompt, temperature=0.1)
        decisions = self._parse_json_safe(raw)

        if not decisions or "actions" not in decisions:
            # Rule-based fallback — always machine-usable
            actions = []
            if metrics["average_coverage"] < COVERAGE_TARGET:
                for s in weak_regions:
                    actions.append({
                        "region":        s["region"],
                        "action":        "increase coverage_weight in GA",
                        "expected_gain": f"+{COVERAGE_TARGET - s.get('coverage_percent',0):.1f}% coverage",
                    })
            if conflicts:
                actions.append({
                    "region":        "global",
                    "action":        "re-run GA with resolved chromosome",
                    "expected_gain": f"eliminate {len(conflicts)} service overlaps",
                })

            # Derive weight adjustments from coverage gap
            cov_gap   = max(0, COVERAGE_TARGET - metrics["average_coverage"])
            cov_boost = min(0.2, cov_gap / 100.0)
            decisions = {
                "actions":    actions,
                "priorities": [
                    f"Raise coverage from {metrics['average_coverage']:.1f}% to {COVERAGE_TARGET}%",
                    f"Eliminate {len(conflicts)} conflict(s)",
                ],
                "weight_adjustments": {
                    "profit_weight":   max(0.3, 0.5 - cov_boost),
                    "coverage_weight": min(0.6, 0.4 + cov_boost),
                    "cost_weight":     0.1,
                },
                "notes": (
                    f"Rule-based fallback: coverage {metrics['average_coverage']:.1f}%, "
                    f"profit ${metrics['total_profit']:,.0f}/week, "
                    f"{len(conflicts)} conflicts."
                ),
            }

        return decisions

    # ================================================================
    # 6. FEEDBACK SIGNALS — GRADIENT (not just binary)
    # ================================================================

    def _generate_feedback_signals(
        self,
        conflicts:      List[Dict],
        metrics:        Dict,
        evaluation:     Dict,
        iteration:      int,
    ) -> Dict:
        """
        Returns gradient signals so the orchestrator can adjust GA weights
        proportionally, not just flip a rerun flag.

        Fields:
          needs_rerun        bool   — should orchestrator loop again?
          rerun_reason       str    — human-readable reason with numbers
          coverage_gap       float  — how far below target (0 if above)
          profit_gap         float  — how far below floor (0 if above)
          conflict_severity  int    — number of unresolved conflicts
          weight_adjustments dict   — direct GA weight deltas to apply
          convergence_score  float  — 0.0 (bad) → 1.0 (converged)
        """
        coverage          = metrics["average_coverage"]
        profit            = metrics["total_profit"]
        coverage_gap      = max(0.0, COVERAGE_TARGET - coverage)
        profit_gap        = max(0.0, PROFIT_FLOOR - profit)
        conflict_severity = len(conflicts)

        # Determine rerun need
        rerun_reasons = []
        if coverage_gap > 0:
            rerun_reasons.append(
                f"coverage {coverage:.1f}% is {coverage_gap:.1f}pp below {COVERAGE_TARGET}% target"
            )
        if profit_gap > 0:
            rerun_reasons.append(
                f"profit ${profit:,.0f} is ${profit_gap:,.0f} below floor"
            )
        if conflict_severity > MAX_CONFLICTS_ALLOWED:
            rerun_reasons.append(
                f"{conflict_severity} service overlap conflict(s) remain"
            )

        # Hard cap on iterations to prevent infinite loops
        at_iteration_cap = iteration >= MAX_RERUN_ITERATIONS - 1
        needs_rerun      = bool(rerun_reasons) and not at_iteration_cap

        if at_iteration_cap and rerun_reasons:
            rerun_reasons.append(
                f"[CAPPED] max iterations ({MAX_RERUN_ITERATIONS}) reached — halting despite gaps"
            )

        rerun_reason = "; ".join(rerun_reasons) if rerun_reasons else "converged"

        # Gradient weight adjustments (proportional to gap)
        cov_boost  = min(0.25, coverage_gap / 100.0 * 1.5)
        prof_boost = min(0.15, profit_gap / 1_000_000 * 0.1) if profit_gap > 0 else 0.0

        weight_adjustments = {
            "profit_weight":   round(max(0.20, 0.50 - cov_boost + prof_boost), 3),
            "coverage_weight": round(min(0.70, 0.40 + cov_boost), 3),
            "cost_weight":     round(max(0.05, 0.10 - prof_boost), 3),
        }

        # Normalise weights to sum = 1.0
        total = sum(weight_adjustments.values())
        weight_adjustments = {k: round(v / total, 3) for k, v in weight_adjustments.items()}

        # Convergence score: 1.0 = perfect, 0.0 = worst case
        cov_score      = min(1.0, coverage / COVERAGE_TARGET)
        profit_score   = 1.0 if profit > PROFIT_FLOOR else 0.0
        conflict_score = 1.0 if conflict_severity == 0 else max(0.0, 1 - conflict_severity * 0.2)
        convergence_score = round((cov_score + profit_score + conflict_score) / 3.0, 3)

        return {
            "needs_rerun":        needs_rerun,
            "rerun_reason":       rerun_reason,
            "coverage_gap":       round(coverage_gap, 2),
            "profit_gap":         round(profit_gap, 2),
            "conflict_severity":  conflict_severity,
            "weight_adjustments": weight_adjustments,
            "convergence_score":  convergence_score,
            "iteration":          iteration,
            "at_iteration_cap":   at_iteration_cap,
            # Legacy binary flags (backward-compat)
            "conflict_count":     conflict_severity,
            "low_coverage":       coverage_gap > 0,
            "low_profit":         profit_gap > 0,
        }

    # ================================================================
    # HELPERS
    # ================================================================

    @staticmethod
    def _parse_json_safe(raw: str) -> Dict:
        """Extract JSON from LLM output, stripping markdown fences."""
        if not raw:
            return {}
        text = raw.strip()
        # Strip ```json ... ``` or ``` ... ```
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Try to extract first {...} block
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    pass
        return {}
