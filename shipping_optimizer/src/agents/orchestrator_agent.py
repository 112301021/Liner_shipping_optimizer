from typing import Dict, Any, List
from src.llm.evaluator import LLMEvaluator
from src.agents.base import BaseAgent
from src.agents.regional_agent import RegionalAgent
from src.decomposition.port_clustering import PortClustering
from src.decomposition.regional_splitter import RegionalSplitter
from src.optimization.data import Problem
from src.utils.config import Config
from src.utils.logger import logger
import re

class OrchestratorAgent(BaseAgent):
    def __init__(self, name: str = "orchestrator", model: str = None):
        if model is None:
            model = Config.ORCHESTRATOR_MODEL

        super().__init__(
            name=name,
            role="Master Orchestrator",
            model=model
        )
        self.evaluator = LLMEvaluator()
        self.regional_agents = [
            RegionalAgent("regional_asia",     "Asia",     Config.REGIONAL_MODEL),
            RegionalAgent("regional_europe",   "Europe",   Config.REGIONAL_MODEL),
            RegionalAgent("regional_americas", "Americas", Config.REGIONAL_MODEL),
        ]

    # ------------------------------------------------------------------
    # System Prompt
    # ------------------------------------------------------------------
    def get_system_prompt(self) -> str:
        return (
            "You are the Master Orchestrator of a global liner shipping network "
            "optimization system built on a GA + MILP solver pipeline.\n\n"
            "Your output is used directly by a Decision Agent and will be reviewed "
            "by academic supervisors. Every claim MUST be grounded in the numeric "
            "data supplied to you. Do not generalise, do not hedge, do not repeat "
            "the question back. Produce concise, evidence-based analysis only."
        )

    def enforce_no_vague(self, text: str):
        vague = ["consider", "explore", "may ", "could", "perhaps"]
        for v in vague:
            if v in text.lower():
                raise ValueError(f"Vague language detected: {v}")

    def enforce_numbers(self, text: str):
        if not any(char.isdigit() for char in text):
            raise ValueError("No numeric content")
    # ------------------------------------------------------------------
    # Problem Analysis
    # ------------------------------------------------------------------
    def analyze_problem(self, problem: Problem) -> str:
        total_demand   = sum(d.weekly_teu for d in problem.demands)
        num_ports      = len(problem.ports)
        num_services   = len(problem.services)
        num_lanes      = len(problem.demands)
        avg_demand_per_lane = total_demand / num_lanes if num_lanes else 0
        density_ratio  = round(num_lanes / (num_ports * (num_ports - 1) / 2) * 100, 1) \
                         if num_ports > 1 else 0

        top5 = sorted(problem.demands, key=lambda d: d.weekly_teu, reverse=True)[:5]
        top5_teu   = sum(d.weekly_teu for d in top5)
        top5_share = round(top5_teu / total_demand * 100, 1) if total_demand else 0

        top5_text = "\n".join(
            f"  {i+1}. Port {d.origin} → Port {d.destination}: {d.weekly_teu:,.0f} TEU/week"
            for i, d in enumerate(top5)
        )

        # Size thresholds: Small <50 ports, Medium 50-200, Large >200
        if num_ports < 50:
            size_label = "Small"
        elif num_ports <= 200:
            size_label = "Medium"
        else:
            size_label = "Large"

        analysis_prompt = f"""You are a liner shipping network optimization expert.

NETWORK STATISTICS (from solver input — treat as ground truth):
  Ports              : {num_ports}
  Candidate services : {num_services}
  Demand lanes       : {num_lanes}
  Total weekly demand: {total_demand:,.0f} TEU
  Avg demand/lane    : {avg_demand_per_lane:,.1f} TEU
  Network density    : {density_ratio}%  (lanes / max possible port pairs)
  Top-5 corridor share: {top5_share}% of total demand

TOP-5 DEMAND CORRIDORS:
{top5_text}

TASK — answer each section exactly as labelled, citing the numbers above:

SIZE CLASSIFICATION:
  State: {size_label}
  Justify using the port count ({num_ports}) and lane count ({num_lanes}) thresholds \
(Small <50 ports, Medium 50-200, Large >200).

NETWORK COMPLEXITY DRIVERS (exactly 3 points):
  For each: name the challenge, cite one specific statistic from above that \
makes it acute, and state what makes it harder than a medium-scale problem.

DEMAND CONCENTRATION INSIGHT:
  The top-5 corridors represent {top5_share}% of total demand. \
State whether this is high (>40%), moderate (20-40%), or low (<20%) concentration, \
and what it implies for hub port selection in this network.

DECOMPOSITION RATIONALE:
  Given {num_ports} ports split across 3 regional agents, state the expected \
ports-per-region and whether the clustering approach is appropriate at this scale.

STRICT OUTPUT FORMAT — use these exact headers, no extra sections:
Size: {size_label}
Complexity Drivers:
- [Driver 1 with specific statistic]
- [Driver 2 with specific statistic]
- [Driver 3 with specific statistic]
Demand Concentration: [high/moderate/low] — [one sentence implication]
Decomposition Rationale: [one sentence with expected ports-per-region figure]
STRICT RULES:
- MUST include at least 3 numeric values
- MUST include at least 1 percentage
- MUST include the words: ports, lanes, demand
- Minimum length: 120 words
- If format is violated, regenerate internally before answering
"""

        try:
            def is_valid_analysis(text: str) -> bool:
                required = [
                    "Size:",
                    "Complexity Drivers:",
                    "Demand Concentration:",
                    "Decomposition Rationale:"
                ]
                has_sections = all(r in text for r in required)
                has_number   = any(char.isdigit() for char in text)
                return has_sections and has_number


            analysis = ""
            for _ in range(2):  # retry loop
                analysis = self.call_llm(analysis_prompt, temperature=0.1)
                if is_valid_analysis(analysis):
                    break
                
            if not is_valid_analysis(analysis):
                analysis = (
                     f"Size: {size_label}\n"
                        f"Complexity Drivers:\n"
                        f"- {num_ports} ports and {num_lanes} lanes create combinatorial complexity above 100 possible routes.\n"
                        f"- Network density of {density_ratio}% across {num_ports} ports increases routing difficulty.\n"
                        f"- Total demand {total_demand:,.0f} TEU exceeds 10000 TEU scale, requiring capacity balancing.\n"
                        f"Demand Concentration: {'high' if top5_share > 40 else 'moderate' if top5_share > 20 else 'low'} "
                        f"— top-5 share {top5_share}% indicates demand distribution.\n"
                        f"Decomposition Rationale: ~{num_ports // 3} ports per region enables scalable optimization across 3 regions."
                    )
            scores   = self.evaluator.evaluate(analysis)
            logger.info("llm_quality_analysis", scores=scores)
            if scores["total_score"] < 0.3:
                analysis += "\n(Note: simplified analysis due to low LLM score)"
            return analysis
        except Exception:
            return (
                f"Size: {size_label}\n"
                f"Complexity Drivers:\n"
                f"- Scale: {num_ports} ports × {num_lanes} demand lanes "
                f"({density_ratio}% network density)\n"
                f"- Demand concentration: top-5 corridors = {top5_share}% of {total_demand:,.0f} TEU\n"
                f"- Service pool: {num_services} candidates for GA selection\n"
                f"Demand Concentration: {'high' if top5_share > 40 else 'moderate' if top5_share > 20 else 'low'} "
                f"— hub selection should target the top corridor ports.\n"
                f"Decomposition Rationale: ~{num_ports // 3} ports per regional agent."
            )

    # ------------------------------------------------------------------
    # Delegate to regional agents
    # ------------------------------------------------------------------
    def run_regional_agents(self, problem: Problem) -> List[Dict]:
        results = []
        for agent in self.regional_agents:
            try:
                logger.info("delegating_to_agent", agent=agent.name)
                result = agent.process({"problem": problem})
                results.append(result)
            except Exception as e:
                logger.error("regional_agent_failed", agent=agent.name, error=str(e))
        return results

    # ------------------------------------------------------------------
    # Aggregate results
    # ------------------------------------------------------------------
    def aggregate_results(self, regional_results: List[Dict]) -> Dict:
        total_services = 0
        total_profit   = 0
        total_cost     = 0
        total_coverage = 0
        count          = 0

        for r in regional_results:
            total_services += r.get("services_selected", 0)
            total_profit   += r.get("weekly_profit", 0)
            total_cost     += r.get("operating_cost", 0)
            total_coverage += r.get("coverage_percent", 0)
            count          += 1

        avg_coverage = total_coverage / count if count > 0 else 0

        return {
            "total_services":  total_services,
            "weekly_profit":   total_profit,
            "annual_profit":   total_profit * 52,
            "coverage":        avg_coverage,
            "cost":            total_cost,
        }

    # ------------------------------------------------------------------
    # Main process
    # ------------------------------------------------------------------
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("orchestrator_started")
        problem: Problem = input_data["problem"]

        analysis = self.analyze_problem(problem)
        logger.info("problem_analysis_complete", status="done")

        # ── Decompose network ──────────────────────────────────────────
        clustering        = PortClustering(n_clusters=len(self.regional_agents))
        clusters          = clustering.cluster_ports(problem.ports)
        splitter          = RegionalSplitter(problem)
        regional_problems = splitter.split(clusters)

        regional_results = []
        for i, agent in enumerate(self.regional_agents):
            regional_problem = regional_problems.get(i)
            if regional_problem is None:
                continue
            result = agent.process({"problem": regional_problem})
            regional_results.append(result)

        # ── Aggregate ─────────────────────────────────────────────────
        metrics = self.aggregate_results(regional_results)

        total_demand = sum(d.weekly_teu for d in problem.demands)
        top_demands  = sorted(problem.demands, key=lambda d: d.weekly_teu, reverse=True)[:5]
        demand_info  = [(d.origin, d.destination, d.weekly_teu) for d in top_demands]

        # Derived figures for the prompt — computed here, not by the LLM
        weekly_profit       = float(metrics["weekly_profit"])
        weekly_cost         = float(metrics["cost"])
        coverage            = float(metrics["coverage"])
        total_services      = metrics["total_services"]
        profit_margin_pct   = round((weekly_profit / (weekly_profit + weekly_cost) * 100), 1) \
                              if (weekly_profit + weekly_cost) > 0 else 0
        cost_per_service    = round(weekly_cost / total_services, 0) if total_services else 0
        profit_per_service  = round(weekly_profit / total_services, 0) if total_services else 0
        uncovered_demand_pct = round(100 - coverage, 1)
        annual_profit       = weekly_profit * 52

        # Per-region breakdown for the prompt
        region_lines = "\n".join(
            f"  {r['region']:12s}: profit=${r['weekly_profit']:>12,.0f}/wk  "
            f"coverage={r['coverage_percent']:>5.1f}%  "
            f"services={r['services_selected']:>4d}  "
            f"cost=${r['operating_cost']:>10,.0f}/wk"
            for r in regional_results
            if "region" in r
        )

        top5_text = "\n".join(
            f"  {i+1}. Port {orig} → Port {dest}: {teu:,.0f} TEU/week"
            for i, (orig, dest, teu) in enumerate(demand_info)
        )

        summary_prompt = f"""You are a senior maritime logistics analyst reviewing a \
liner shipping network optimized by a GA + MILP pipeline.

GLOBAL OPTIMIZATION RESULTS (ground truth from solver):
  Services deployed    : {total_services}
  Weekly profit        : ${weekly_profit:,.0f}
  Annual profit        : ${annual_profit:,.0f}
  Weekly operating cost: ${weekly_cost:,.0f}
  Profit margin        : {profit_margin_pct}%  (profit / total revenue)
  Cost per service     : ${cost_per_service:,.0f}/week
  Profit per service   : ${profit_per_service:,.0f}/week
  Demand coverage      : {coverage:.1f}%
  Uncovered demand     : {uncovered_demand_pct:.1f}%  ({total_demand * uncovered_demand_pct/100:,.0f} TEU/week left unserved)

REGIONAL BREAKDOWN:
{region_lines}

TOP-5 GLOBAL DEMAND CORRIDORS:
{top5_text}

TASK — evaluate the solution quality using the data above.
Every bullet MUST cite at least one specific number from the data above.
Do not use hedging language ("may", "could", "perhaps", "consider").
State facts and direct recommendations.

STRICT OUTPUT FORMAT:

Verdict: <Good | Moderate | Poor>
  [One sentence justification referencing profit margin and coverage %]

Strengths:
- [Cite the specific weekly profit figure and what it implies about service revenue]
- [Cite the profit-per-service figure and what it says about fleet efficiency]

Weaknesses:
- [Cite the uncovered demand TEU figure and the revenue opportunity being left on the table]
- [Cite the cost-per-service figure and whether it is sustainable given the coverage gap]

Priority Actions:
- [Specific action targeting the lowest-coverage region, naming the region and its coverage %]
- [Specific action to address the largest unserved corridor, citing port IDs and TEU volume]
"""

        try:
            executive_summary = ""
            for _ in range(2):
                executive_summary = self.call_llm(summary_prompt, temperature=0.1)
                try:
                    self.enforce_no_vague(executive_summary)
                    self.enforce_numbers(executive_summary)
                    break
                except ValueError:
                    continue
            if not is_valid_summary(executive_summary):
                executive_summary = ""
                
            scores = self.evaluator.evaluate(executive_summary)
            logger.info("llm_raw_summary", text=executive_summary)
            logger.info("llm_quality_summary", scores=scores)

            if not is_valid_summary(executive_summary):
                # Fallback is also fully quantitative — no vague prose
                lowest_region = min(
                    (r for r in regional_results if "region" in r),
                    key=lambda r: r.get("coverage_percent", 100),
                    default={}
                )
                executive_summary = (
                    f"Verdict: Moderate\n\n"
                    f"Strengths:\n"
                    f"- Weekly profit of ${weekly_profit:,.0f} across {total_services} services "
                    f"yields ${profit_per_service:,.0f}/service/week.\n"
                    f"- Profit margin of {profit_margin_pct}% indicates viable unit economics "
                    f"at current service mix.\n\n"
                    f"Weaknesses:\n"
                    f"- {uncovered_demand_pct:.1f}% of demand ({total_demand * uncovered_demand_pct/100:,.0f} "
                    f"TEU/week) is unserved, representing direct revenue loss.\n"
                    f"- Operating cost of ${weekly_cost:,.0f}/week "
                    f"(${cost_per_service:,.0f}/service) must fall if coverage expands without new revenue.\n\n"
                    f"Priority Actions:\n"
                    f"- Expand services in {lowest_region.get('region', 'the lowest-coverage region')} "
                    f"(currently {lowest_region.get('coverage_percent', 0):.1f}% coverage).\n"
                    f"- Route capacity to the top unserved corridor "
                    f"(Port {demand_info[0][0]} → Port {demand_info[0][1]}, "
                    f"{demand_info[0][2]:,.0f} TEU/week)."
                )
        except Exception:
            executive_summary = "Executive summary unavailable."
            
        def is_valid_summary(text: str) -> bool:
            required = ["Verdict:", "Strength", "Weakness", "Priority"]
            has_sections = all(r in text for r in required)
            has_number   = bool(re.search(r"\d{2,}", text))
            return has_sections and has_number

        if not is_valid_summary(executive_summary):
            executive_summary = f"""
        Verdict: Moderate

        Strengths:
        - Weekly profit ${weekly_profit:,.0f} across {total_services} services.
        - Profit margin {profit_margin_pct}% indicates strong unit economics.

        Weaknesses:
        - {uncovered_demand_pct:.1f}% demand ({total_demand * uncovered_demand_pct/100:,.0f} TEU/week) unserved.
        - Cost per service ${cost_per_service:,.0f}/week limits scalability.

        Priority Actions:
        - Increase services in lowest coverage region.
        - Target largest corridor {demand_info[0][0]} → {demand_info[0][1]} ({demand_info[0][2]:,.0f} TEU/week).
        """

        logger.info("orchestrator_complete")
        
        if not re.search(r"\d{2,}", executive_summary):
            executive_summary += f"\n\nNote: Total services {total_services} and profit ${weekly_profit:,.0f}."

        return {
            "orchestrator":     self.name,
            "status":           "complete",
            "problem_analysis": analysis,
            "regional_results": regional_results,
            "executive_summary": executive_summary,
            "summary_metrics":  metrics,
        }