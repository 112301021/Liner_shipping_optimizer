import re
import time
import logging
from typing import Dict, Any, List
from src.llm.evaluator                  import LLMEvaluator
from src.agents.base                    import BaseAgent
from src.agents.service_generator_agent import ServiceGeneratorAgent
from src.optimization.data              import Problem, Service
from src.optimization.hierarchical_ga   import HierarchicalGA
from src.optimization.hub_milp          import HubMILP
from src.services.hub_detector          import HubDetector

logger = logging.getLogger(__name__)

# ── Shared cost constants — identical in GA and MILP ──────────────────
TRANSSHIP_COST_PER_TEU = 80.0
PORT_COST_PER_TEU      = 15.0
ALPHA_UNSERVED         = 300.0
MIN_COVERAGE_FLOOR     = 0.0    
MAX_TRANSFER_PAIRS     = 2000   

class RegionalAgent(BaseAgent):

    def __init__(self, name: str, region: str, model: str):
        super().__init__(name=name, role=f"Regional Optimizer - {region}", model=model)
        self.region    = region
        self.evaluator = LLMEvaluator()

    def get_system_prompt(self) -> str:
        return (
            f"You are a liner shipping network optimisation analyst for the {self.region} region.\n\n"
            "Your output feeds directly into a Decision Agent reviewed by academic supervisors.\n"
            "1. Every claim must cite a specific number from the data.\n"
            "2. No vague language: 'consider', 'explore', 'may', 'could potentially'.\n"
            "3. Strategy reasons must name specific port IDs or TEU volumes.\n"
            "4. Improvement actions must be specific and measurable."
        )

    def is_valid_explanation(self, text: str) -> bool:
        required = ["Verdict:", "Strength", "Weakness", "Improvement"]
        return all(r in text for r in required) and bool(re.search(r"\d{2,}", text))

    # ------------------------------------------------------------------ #
    #  Hub-based cluster decomposition                                      #
    # ------------------------------------------------------------------ #
    def split_by_hubs(self, problem: Problem, num_hubs: int = 5) -> Dict:
        hub_detector = HubDetector(problem)
        hubs         = hub_detector.detect_hubs(top_k=num_hubs)
        clusters     = {h: [] for h in hubs}
        for p in problem.ports:
            closest_hub = min(
                hubs,
                key=lambda h: problem.distance_matrix.get(h, {}).get(p.id, 1e9),
            )
            clusters[closest_hub].append(p)
        return clusters

    # ------------------------------------------------------------------ #
    #  Smart service filter — raised cap, same margin check                 #
    # ------------------------------------------------------------------ #
    def _filter_services(self, problem: Problem) -> Problem:
        """
        Keep services covering demand corridors with positive margin.
        """
        corridor_set = {(d.origin, d.destination) for d in problem.demands}
        kept = []
        for svc in problem.services:
            port_set = set(svc.ports)
            covers   = any(o in port_set and d in port_set for (o, d) in corridor_set)
            margin   = (svc.capacity * 0.5 * 150) > svc.weekly_cost
            if covers and margin:
                kept.append(svc)

        num_ports    = len(problem.ports)
        max_services = max(400, num_ports)
        kept = sorted(kept, key=lambda s: s.capacity / (s.weekly_cost + 1), reverse=True)[:max_services]

        problem.services = kept
        logger.info("services_filtered", region=self.region, count=len(kept))
        return problem

    # ------------------------------------------------------------------ #
    #  Main pipeline                                                        #
    # ------------------------------------------------------------------ #
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.perf_counter()
        logger.info("regional_agent_started", agent=self.name, region=self.region)
        problem: Problem = input_data["problem"]

        # Capture regional total demand BEFORE any splitting/modification
        total_demand = sum(d.weekly_teu for d in problem.demands)
        num_ports    = len(problem.ports)
        num_lanes    = len(problem.demands)
        avg_demand   = total_demand / num_lanes if num_lanes else 0
        median_demand = sorted([d.weekly_teu for d in problem.demands])[num_lanes // 2] if num_lanes else 0

        top_demands  = sorted(problem.demands, key=lambda d: d.weekly_teu, reverse=True)
        top5         = top_demands[:5]
        top3_teu     = sum(d.weekly_teu for d in top_demands[:3])
        top3_share   = round(top3_teu / total_demand * 100, 1) if total_demand else 0

        corridor_table = "\n".join(
            f"  {i+1}. Port {d.origin:>5} -> Port {d.destination:>5}: "
            f"{d.weekly_teu:>8,.0f} TEU/wk  "
            f"({d.weekly_teu / total_demand * 100:.1f}% of regional demand)"
            for i, d in enumerate(top5)
        )

        hub_detector  = HubDetector(problem)
        detected_hubs = hub_detector.detect_hubs(top_k=5)
        hub_ids_str   = ", ".join(str(h) for h in detected_hubs)

        # Strategy based on demand dispersion 
        if median_demand <= 10 and num_lanes > 500:
            strat_code = "C"
            strat_name = "hybrid"
            decision_rule = (
                f"Select C (Hybrid): median demand {median_demand} TEU/lane with {num_lanes} lanes "
                f"-> consolidation via hub routing essential for low-demand corridors."
            )
        elif top3_share > 35:
            strat_code = "A"
            strat_name = "hub_and_spoke"
            decision_rule = f"Select A (Hub-and-spoke): top-3 share {top3_share}% > 35%."
        else:
            strat_code = "C"
            strat_name = "hybrid"
            decision_rule = (
                f"Select C (Hybrid): top-3 share {top3_share}% with avg {avg_demand:.1f} TEU/lane."
            )

        strategy_prompt = (
            f"REGIONAL DATA - {self.region.upper()}:\n"
            f"  Ports: {num_ports}, Lanes: {num_lanes}, Median demand: {median_demand} TEU/lane\n"
            f"  Total demand: {total_demand:,.0f} TEU/wk, Top-3 share: {top3_share}%\n"
            f"  Hub ports: [{hub_ids_str}]\n\n"
            f"TOP-5 CORRIDORS:\n{corridor_table}\n\n"
            f"DECISION RULE: {decision_rule}\n\n"
            f"STRICT FORMAT:\n"
            f"Strategy: <A | B | C>\n"
            f"Selected: <hub_and_spoke | direct | hybrid>\n"
            f"Reason 1: [cite median demand {median_demand} TEU/lane and >=1 port ID]\n"
            f"Reason 2: [cite port count {num_ports} and lane count {num_lanes}]\n"
            f"Hub Ports: [{hub_ids_str}]"
        )

        try:
            strategy = self.call_llm(strategy_prompt, temperature=0.1)
            if not any(c.isdigit() for c in strategy):
                strategy += f"\nReason 3: Demand {total_demand:,.0f} TEU across {num_ports} ports."
        except Exception:
            strategy = (
                f"Strategy: {strat_code}\nSelected: {strat_name}\n"
                f"Reason 1: Median demand {median_demand} TEU/lane across {num_lanes} lanes "
                f"-> hub consolidation required for {num_lanes-500} low-demand corridors.\n"
                f"Reason 2: {num_ports} ports x {num_lanes} lanes -> hub ports [{hub_ids_str}].\n"
                f"Hub Ports: [{hub_ids_str}]"
            )

        # ── Service generation ─────────────────────────────────────────
        svc_agent  = ServiceGeneratorAgent(name="svc_gen", model=self.model)
        svc_result = svc_agent.process({"problem": problem})
        services   = svc_result["services"]
        services_generated = len(services)

        norm: List[Service] = []
        for i, s in enumerate(services):
            if isinstance(s, Service):
                norm.append(s)
            else:
                norm.append(Service(
                    id=s.get("id", i), ports=s["ports"],
                    capacity=s.get("capacity", 5000),
                    weekly_cost=s.get("weekly_cost", 150_000),
                    cycle_time=s.get("cycle_time", 14),
                ))
        problem.services = norm

        # ── Smart service filter ───────────────────────────────────────
        problem           = self._filter_services(problem)
        services_filtered = len(problem.services)

        # ── HierarchicalGA ─────────────────────────────────────────────
        logger.info("hierarchical_ga_started")
        ga = HierarchicalGA(
            problem,
            w_profit = getattr(problem, "profit_weight", 0.5),
            w_coverage = getattr(problem, "coverage_weight", 0.4),
            w_cost = getattr(problem, "cost_weight", 0.1),
            alpha_unserved         = ALPHA_UNSERVED,
            max_runtime_sec        = 55.0,
            transship_cost_per_teu = TRANSSHIP_COST_PER_TEU,
            port_cost_per_teu      = PORT_COST_PER_TEU,
        )
        chromosome        = ga.run()
        services_selected = sum(chromosome["services"])
        logger.info("ga_complete", services_selected=services_selected)
        
        # ── MILP decomposition by hub clusters ─────────────────────────
        logger.info("milp_decomposition_started")
        clusters        = self.split_by_hubs(problem)
        cluster_results = []

        for hub, ports in clusters.items():
            cluster_port_ids = {p.id for p in ports}
            cluster_demands  = [
                d for d in problem.demands
                if d.origin in cluster_port_ids or d.destination in cluster_port_ids
            ]
            if not cluster_demands:
                continue

            sub = Problem(
                ports           = ports,
                services        = problem.services,
                demands         = cluster_demands,
                distance_matrix = problem.distance_matrix,
            )
            milp = HubMILP(
                sub,
                chromosome,
                transship_cost_per_teu = TRANSSHIP_COST_PER_TEU,
                port_cost_per_teu      = PORT_COST_PER_TEU,
                alpha_unserved         = ALPHA_UNSERVED,
                min_coverage           = MIN_COVERAGE_FLOOR,
                max_transfer_pairs     = MAX_TRANSFER_PAIRS,
            )
            cluster_results.append(milp.solve())

        # ── Aggregate — use regional total_demand as denominator ────────
        # (Not sum of cluster total_demand which double-counts cross-cluster OD)
        profit         = sum(r["profit"]           for r in cluster_results)
        operating_cost = sum(r["cost"]             for r in cluster_results)
        transship_cost = sum(r["transship_cost"]   for r in cluster_results)
        port_cost      = sum(r["port_cost"]        for r in cluster_results)
        total_cost     = sum(r["total_cost"]       for r in cluster_results)
        satisfied      = sum(r["satisfied_demand"] for r in cluster_results)
        unserved_teu   = sum(r["unserved_demand"]  for r in cluster_results)

        # Cap satisfied at total_demand to avoid >100% coverage
        satisfied = min(satisfied, total_demand)
        coverage  = satisfied / total_demand * 100 if total_demand else 0.0

        # Derived metrics
        uncovered_pct      = round(100 - coverage, 1)
        profit_per_service = round(profit / services_selected, 0) if services_selected else 0
        cost_per_service   = round(total_cost / services_selected, 0) if services_selected else 0
        profit_margin_pct  = round(
            profit / (profit + total_cost) * 100, 1
        ) if (profit + total_cost) > 0 else 0
        uncovered_teu_abs  = total_demand * (100 - coverage) / 100

        top_unserved  = top_demands[0] if top_demands else None
        unserved_line = (
            f"Port {top_unserved.origin} -> Port {top_unserved.destination}: "
            f"{top_unserved.weekly_teu:,.0f} TEU/week"
            if top_unserved else "N/A"
        )

        # ── LLM explanation ────────────────────────────────────────────
        explanation_prompt = (
            f"Maritime logistics analyst evaluating {self.region.upper()} region.\n\n"
            f"SOLVER RESULTS:\n"
            f"  Services generated/filtered/selected: {services_generated}/{services_filtered}/{services_selected}\n"
            f"  Weekly profit: ${profit:,.0f} | Annual: ${profit * 52:,.0f}\n"
            f"  Cost: Operating ${operating_cost:,.0f} | Transship ${transship_cost:,.0f} | Port ${port_cost:,.0f}\n"
            f"  Margin: {profit_margin_pct}% | Profit/svc: ${profit_per_service:,.0f}/wk\n"
            f"  Coverage: {coverage:.1f}% | Unserved: {uncovered_pct:.1f}% ({unserved_teu:,.0f} TEU/wk)\n"
            f"  Hub ports: [{hub_ids_str}]\n\n"
            f"TOP-5 CORRIDORS:\n{corridor_table}\n\n"
            f"STRICT FORMAT:\n"
            f"Verdict: <Good | Moderate | Poor>\n"
            f"  [Cite margin {profit_margin_pct}% and coverage {coverage:.1f}%]\n\n"
            f"Strengths:\n"
            f"- [Cite profit ${profit:,.0f} and profit/service]\n"
            f"- [Cite coverage {coverage:.1f}% and satisfied TEU]\n\n"
            f"Weaknesses:\n"
            f"- [Cite unserved {uncovered_pct:.1f}% = {unserved_teu:,.0f} TEU/wk]\n"
            f"- [Cite transship ${transship_cost:,.0f} and port ${port_cost:,.0f}]\n\n"
            f"Improvement Actions:\n"
            f"- [Action 1: target {unserved_line}]\n"
            f"- [Action 2: hub [{hub_ids_str}] expansion for {uncovered_pct:.1f}% gap]"
        )

        try:
            explanation = ""
            for _ in range(2):
                explanation = self.call_llm(explanation_prompt, temperature=0.1)
                if self.is_valid_explanation(explanation):
                    break
            if not self.is_valid_explanation(explanation):
                raise ValueError("invalid")
        except Exception:
            verdict = (
                "Good" if profit_margin_pct > 60 else
                "Moderate" if profit_margin_pct > 30 else "Poor"
            )
            explanation = (
                f"Verdict: {verdict}\n"
                f"  Profit margin {profit_margin_pct}% with coverage {coverage:.1f}%.\n\n"
                f"Strengths:\n"
                f"- Weekly profit ${profit:,.0f} ({services_selected} services) -> "
                f"${profit_per_service:,.0f}/service/week.\n"
                f"- Satisfied {satisfied:,.0f} TEU/wk at {coverage:.1f}% coverage.\n\n"
                f"Weaknesses:\n"
                f"- {uncovered_pct:.1f}% unserved ({unserved_teu:,.0f} TEU/wk).\n"
                f"- Transshipment ${transship_cost:,.0f} + port ${port_cost:,.0f}/wk.\n\n"
                f"Improvement Actions:\n"
                f"- Add services to {unserved_line} corridor.\n"
                f"- Expand hub [{hub_ids_str}] by {max(3, int(services_selected * 0.1))} services."
            )

        elapsed = round(time.perf_counter() - t0, 2)
        logger.info(
            "regional_agent_complete",
            region=self.region, profit=profit, coverage=coverage, elapsed=elapsed,
        )

        return {
            "agent":               self.name,
            "region":              self.region,
            "status":              "Optimal",
            "services_generated":  services_generated,
            "services_filtered":   services_filtered,
            "services_selected":   services_selected,
            "weekly_profit":       profit,
            "annual_profit":       profit * 52,
            "operating_cost":      operating_cost,
            "transship_cost":      transship_cost,
            "port_cost":           port_cost,
            "total_cost":          total_cost,
            "coverage_percent":    coverage,
            "satisfied_demand":    satisfied,
            "unserved_demand":     unserved_teu,
            "total_demand":        total_demand,
            "profit_margin_pct":   profit_margin_pct,
            "profit_per_service":  profit_per_service,
            "cost_per_service":    cost_per_service,
            "uncovered_teu":       uncovered_teu_abs,
            "hub_ports":           detected_hubs,
            "strategy":            strategy,
            "explanation":         explanation,
            "elapsed_sec":         elapsed,
        }