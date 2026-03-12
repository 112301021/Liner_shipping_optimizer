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

    # ------------------------------------------------
    # System Prompt
    # ------------------------------------------------
    def get_system_prompt(self) -> str:

        return """
You are a shipping network design expert.

Your role:
- Identify hub ports
- Design efficient liner shipping routes
- Maximize vessel utilization
- Reduce operating costs

Prefer hub-and-spoke routes and avoid redundant services.
"""

    # ------------------------------------------------
    # Generate candidate services
    # ------------------------------------------------
    def generate_services(self, problem: Problem) -> List[Service]:

        logger.info(
            "service_generation_started",
            ports=len(problem.ports),
            demands=len(problem.demands)
        )

        # -------------------------
        # Step 1: detect hubs
        # -------------------------
        hub_detector = HubDetector(problem)

        hubs = hub_detector.detect_hubs(top_k=10)

        logger.info(
            "hubs_detected",
            num_hubs=len(hubs)
        )

        # -------------------------
        # Step 2: base candidate services
        # -------------------------
        generator = CandidateServiceGenerator(problem)

        services = generator.generate_services(
            num_services=200
        )

        # -------------------------
        # Step 3: demand-driven services
        # -------------------------
        # connect top demand lanes

        top_demands = sorted(
            problem.demands,
            key=lambda d: d.weekly_teu,
            reverse=True
        )[:50]

        service_id = len(services)

        for d in top_demands:

            route = [d.origin, d.destination, d.origin]

            services.append(
                Service(
                    id=service_id,
                    ports=route,
                    capacity=8000,
                    weekly_cost=150000,
                    cycle_time=14
                )
            )

            service_id += 1

        logger.info(
            "demand_services_added",
            count=len(top_demands)
        )

        # -------------------------
        # Step 4: hub-to-hub trunk routes
        # -------------------------
        for i in range(len(hubs)):

            for j in range(i + 1, len(hubs)):

                route = [hubs[i], hubs[j], hubs[i]]

                services.append(
                    Service(
                        id=service_id,
                        ports=route,
                        capacity=12000,
                        weekly_cost=200000,
                        cycle_time=14
                    )
                )

                service_id += 1

        logger.info(
            "hub_trunk_services_added",
            count=len(hubs) * (len(hubs) - 1) // 2
        )

        logger.info(
            "candidate_services_generated",
            num_services=len(services)
        )

        return services

    # ------------------------------------------------
    # Main pipeline
    # ------------------------------------------------
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:

        logger.info(
            "service_generator_agent_started",
            agent=self.name
        )

        problem: Problem = input_data["problem"]

        # -------------------------
        # LLM strategy (optional)
        # -------------------------
        prompt = f"""
We are designing liner shipping services.

Ports: {len(problem.ports)}
Demand lanes: {len(problem.demands)}

Should we prioritize:

a) hub-and-spoke routes
b) direct routes
c) mixed strategy

Answer in 1 sentence.
"""

        try:
            strategy = self.call_llm(prompt, temperature=0.5)
        except Exception:
            strategy = "Hybrid hub-and-spoke strategy recommended."

        # -------------------------
        # Generate services
        # -------------------------
        services = self.generate_services(problem)

        # attach to problem
        problem.services = services

        logger.info(
            "services_attached_to_problem",
            count=len(services)
        )

        return {
            "agent": self.name,
            "strategy": strategy,
            "services_generated": len(services),
            "services": services
        }