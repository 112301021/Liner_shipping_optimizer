from typing import Dict, Any, List

from src.agents.base import BaseAgent
from src.services.hub_detector import HubDetector
from src.services.candidate_service_generator import CandidateServiceGenerator
from src.optimization.data import Problem, Service
from src.utils.logger import logger


class ServiceGeneratorAgent(BaseAgent):

    def __init__(self, name: str, model: str):
        super().__init__(
            name=name,
            role="Shipping Service Generator",
            model=model
        )

    # ------------------------------------------------------------------
    # System Prompt
    # ------------------------------------------------------------------
    def get_system_prompt(self) -> str:
        return (
            "You are a liner shipping service design specialist.\n\n"
            "You advise on which service archetypes to generate for a given port network. "
            "Your recommendations must be grounded in the network statistics you are given. "
            "Every recommendation must cite a specific number. "
            "Do not use vague language. Do not repeat the question."
        )

    # ------------------------------------------------------------------
    # Generate candidate services (deterministic — unchanged)
    # ------------------------------------------------------------------
    def generate_services(self, problem: Problem) -> List[Service]:
        logger.info(
            "service_generation_started",
            ports=len(problem.ports),
            demands=len(problem.demands),
        )

        # Step 1: detect hubs
        hub_detector = HubDetector(problem)
        hubs         = hub_detector.detect_hubs(top_k=10)
        logger.info("hubs_detected", num_hubs=len(hubs))

        # Step 2: base candidate services
        generator = CandidateServiceGenerator(problem)
        services  = generator.generate_services(num_services=200)

        # Step 3: demand-driven direct services for top-50 corridors
        top_demands = sorted(problem.demands, key=lambda d: d.weekly_teu, reverse=True)[:50]
        service_id  = len(services)
        for d in top_demands:
            services.append(Service(
                id=service_id,
                ports=[d.origin, d.destination, d.origin],
                capacity=8000,
                weekly_cost=150000,
                cycle_time=14,
            ))
            service_id += 1
        logger.info("demand_services_added", count=len(top_demands))

        # Step 4: hub-to-hub trunk routes
        for i in range(len(hubs)):
            for j in range(i + 1, len(hubs)):
                services.append(Service(
                    id=service_id,
                    ports=[hubs[i], hubs[j], hubs[i]],
                    capacity=12000,
                    weekly_cost=200000,
                    cycle_time=14,
                ))
                service_id += 1
        logger.info(
            "hub_trunk_services_added",
            count=len(hubs) * (len(hubs) - 1) // 2,
        )

        logger.info("candidate_services_generated", num_services=len(services))
        return services

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("service_generator_agent_started", agent=self.name)

        problem: Problem = input_data["problem"]

        # ── Pre-compute statistics for the LLM ────────────────────────
        num_ports    = len(problem.ports)
        num_lanes    = len(problem.demands)
        total_demand = sum(d.weekly_teu for d in problem.demands)
        avg_demand   = total_demand / num_lanes if num_lanes else 0

        top_demands  = sorted(problem.demands, key=lambda d: d.weekly_teu, reverse=True)
        top3_teu     = sum(d.weekly_teu for d in top_demands[:3])
        top3_share   = round(top3_teu / total_demand * 100, 1) if total_demand else 0
        top10_share  = round(
            sum(d.weekly_teu for d in top_demands[:10]) / total_demand * 100, 1
        ) if total_demand else 0

        # Hub detection is deterministic — run it now so we can cite it in the prompt
        hub_detector  = HubDetector(problem)
        hubs          = hub_detector.detect_hubs(top_k=10)
        hub_ids_str   = ", ".join(str(h) for h in hubs)
        num_trunk     = len(hubs) * (len(hubs) - 1) // 2
        num_demand_svc = min(50, num_lanes)

        corridor_table = "\n".join(
            f"  {i+1}. Port {d.origin:>5} → Port {d.destination:>5}: "
            f"{d.weekly_teu:>8,.0f} TEU/wk"
            for i, d in enumerate(top_demands[:5])
        )

        # Determine dominant service archetype from concentration ratio
        if top3_share > 35:
            archetype_recommendation = (
                "HUB-AND-SPOKE DOMINANT: top-3 corridors hold {top3_share}% of demand — "
                "hub trunk routes between [{hub_ids_str}] should form the backbone; "
                "feeder spokes connect remaining {rem} ports."
            ).format(top3_share=top3_share, hub_ids_str=hub_ids_str, rem=num_ports - len(hubs))
        elif top3_share < 20:
            archetype_recommendation = (
                "DIRECT SERVICES DOMINANT: top-3 corridors hold only {top3_share}% of demand — "
                "point-to-point services on the top-50 corridors will capture dispersed demand "
                "more efficiently than routing through hubs."
            ).format(top3_share=top3_share)
        else:
            archetype_recommendation = (
                "HYBRID: top-3 corridors hold {top3_share}% of demand — "
                "{num_trunk} hub trunk routes provide the backbone; "
                "{num_demand_svc} demand-driven direct services cover residual lanes."
            ).format(
                top3_share=top3_share,
                num_trunk=num_trunk,
                num_demand_svc=num_demand_svc,
            )

        prompt = f"""You are advising a liner shipping service design pipeline for a \
{num_ports}-port network.

NETWORK STATISTICS (ground truth):
  Ports               : {num_ports}
  Demand lanes        : {num_lanes}
  Total weekly demand : {total_demand:,.0f} TEU
  Avg demand per lane : {avg_demand:,.1f} TEU
  Top-3 corridor share: {top3_share}%
  Top-10 corridor share: {top10_share}%
  Detected hub ports  : [{hub_ids_str}]  ({len(hubs)} hubs)

TOP-5 DEMAND CORRIDORS:
{corridor_table}

SERVICE POOL TO BE GENERATED:
  Base candidate services  : 200  (from heuristic route generator)
  Demand-driven directs    : {num_demand_svc}  (one per top-{num_demand_svc} corridor)
  Hub trunk routes         : {num_trunk}  (all hub-pair combinations)
  Total candidate pool     : ~{200 + num_demand_svc + num_trunk}

ARCHETYPE RECOMMENDATION (derived from concentration ratio):
  {archetype_recommendation}

TASK — confirm or correct the archetype recommendation above.
State your answer in exactly 2 sentences.
Sentence 1: Confirm which archetype is correct and cite the top-3 share ({top3_share}%) \
and total demand ({total_demand:,.0f} TEU).
Sentence 2: State the expected GA selection pressure — i.e., out of ~{200 + num_demand_svc + num_trunk} \
candidates, approximately how many should the GA retain and why, citing the {num_ports} port count.
"""

        try:
            strategy = self.call_llm(prompt, temperature=0.1)
        except Exception:
            strategy = (
                f"{archetype_recommendation} "
                f"With ~{200 + num_demand_svc + num_trunk} candidates across {num_ports} ports, "
                f"the GA should retain approximately {max(50, num_ports // 2)} services "
                f"to balance coverage and operating cost."
            )

        # ── Generate services (deterministic) ─────────────────────────
        services = self.generate_services(problem)
        problem.services = services

        logger.info("services_attached_to_problem", count=len(services))

        return {
            "agent":              self.name,
            "strategy":           strategy,
            "services_generated": len(services),
            "services":           services,
        }