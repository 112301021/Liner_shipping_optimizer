"""
Test Regional Agent
"""

import json
import sys
from pathlib import Path
from src.data.network_loader import NetworkLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.regional_agent import RegionalAgent
from src.optimization.data import Problem, Port, Service, Demand
from src.utils.config import Config


def load_problem(filename):

    with open(filename) as f:
        data = json.load(f)

    ports = [Port(**p) for p in data["ports"]]
    services = [Service(**s) for s in data["services"]]
    demands = [Demand(**d) for d in data["demands"]]
    loader = NetworkLoader()
    distance_matrix = loader.load_distance_matrix()

    return Problem(ports=ports, services=services, demands=demands, distance_matrix=distance_matrix)


def test_regional_agent():

    print("\n" + "="*70)
    print("TESTING REGIONAL AGENT")
    print("="*70)

    agent = RegionalAgent(
        name="regional_asia",
        region="Asia",
        model=Config.REGIONAL_MODEL
    )

    problem = load_problem("data/datasets/large_shipping_problem.json")

    result = agent.process({"problem": problem})

    print(f"\nservices_generated: {result['services_generated']}")
    print(f"services_filtered: {result['services_filtered']}")
    print(f"services_selected: {result['services_selected']}")
    print(f"weekly_profit: ${result['weekly_profit']:,.0f}")
    print(f"operating_cost: ${result['operating_cost']:,.0f}")
    print(f"coverage: {result['coverage_percent']:.1f}%")


if __name__ == "__main__":
    test_regional_agent()
