"""
Test Orchestrator Agent - Full system integration
"""

import json
import sys
from pathlib import Path

# allow importing src modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.data.network_loader import NetworkLoader
from src.agents.orchestrator_agent import OrchestratorAgent
from src.optimization.data import Problem, Port, Service, Demand


# ------------------------------------------------
# Load problem from JSON
# ------------------------------------------------
def load_problem(filename: str) -> Problem:

    with open(filename) as f:
        data = json.load(f)

    ports = [Port(**p) for p in data["ports"]]
    services = [Service(**s) for s in data["services"]]
    demands = [Demand(**d) for d in data["demands"]]
    loader = NetworkLoader()
    distance_matrix = loader.load_distance_matrix()

    return Problem(
        ports=ports,
        services=services,
        demands=demands,
        distance_matrix=distance_matrix
    )


# ------------------------------------------------
# Main test
# ------------------------------------------------
def test_orchestrator():

    print("\n" + "=" * 70)
    print("TESTING COMPLETE MULTI-AGENT SYSTEM")
    print("=" * 70)

    # ------------------------------------------------
    # Step 1: Create orchestrator
    # ------------------------------------------------
    print("\n1️⃣ Creating Orchestrator Agent...")

    orchestrator = OrchestratorAgent()

    print("✓ Orchestrator created")
    print("✓ Regional agents initialized")

    # ------------------------------------------------
    # Step 2: Load dataset
    # ------------------------------------------------
    print("\n2️⃣ Loading optimization problem...")

    dataset = "data/datasets/large_shipping_problem.json"

    problem = load_problem(dataset)

    print(f"✓ Ports: {len(problem.ports)}")
    print(f"✓ Candidate services: {len(problem.services)}")
    print(f"✓ Demand lanes: {len(problem.demands)}")

    total_demand = sum(d.weekly_teu for d in problem.demands)

    print(f"✓ Total weekly demand: {total_demand:,.0f} TEU")

    # ------------------------------------------------
    # Step 3: Run optimization
    # ------------------------------------------------
    print("\n3️⃣ Running complete optimization...")

    print("Pipeline:")
    print("→ Orchestrator analyzes problem")
    print("→ Regional agents run optimization")
    print("→ GA selects services")
    print("→ MILP optimizes flows")
    print("→ Agents generate explanations")
    print("→ Orchestrator compiles summary")

    print("\nPlease wait...\n")

    result = orchestrator.process({"problem": problem})

    # ------------------------------------------------
    # Display results
    # ------------------------------------------------
    print("\n" + "=" * 70)
    print("OPTIMIZATION COMPLETE")
    print("=" * 70)

    print("\n📊 PROBLEM ANALYSIS")
    print(result["problem_analysis"])

    metrics = result["summary_metrics"]

    print("\n📈 SUMMARY METRICS")
    print(f"Services deployed: {metrics['total_services']}")
    print(f"Weekly profit: ${metrics['weekly_profit']:,.0f}")
    print(f"Annual profit: ${metrics['annual_profit']:,.0f}")
    print(f"Demand coverage: {metrics['coverage']:.1f}%")
    print(f"Operating cost: ${metrics['cost']:,.0f}/week")

    print("\n🧠 REGIONAL AGENT RESULTS")

    for r in result["regional_results"]:
        print(f"\nRegion: {r['region']}")
        print(f"Strategy: {r['strategy']}")
        print(f"Explanation: {r['explanation']}")

    print("\n📋 EXECUTIVE SUMMARY")
    print(result["executive_summary"])

    print("\n" + "=" * 70)

    # ------------------------------------------------
    # Assertions (robust)
    # ------------------------------------------------
    assert result["status"] == "complete"
    assert "summary_metrics" in result
    assert "regional_results" in result

    print("\n✅ Orchestrator integration test passed!")
    print("🚀 Multi-Agent Optimization System operational")

    return result


# ------------------------------------------------
# Run manually
# ------------------------------------------------
if __name__ == "__main__":
    test_orchestrator()