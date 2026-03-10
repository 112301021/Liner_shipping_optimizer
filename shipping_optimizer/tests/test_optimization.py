import json
import sys
import time
from pathlib import Path

# Allow importing src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.optimization.data import Problem, Port, Service, Demand
from src.optimization.simple_ga import SimpleGA
from src.optimization.simple_milp import SimpleMilp


# -------------------------------------------------
# Load dataset
# -------------------------------------------------
def load_problem(filename: str) -> Problem:

    if not Path(filename).exists():
        raise FileNotFoundError(f"Dataset not found: {filename}")

    with open(filename) as f:
        data = json.load(f)

    ports = [Port(**p) for p in data["ports"]]
    services = [Service(**s) for s in data["services"]]
    demands = [Demand(**d) for d in data["demands"]]

    return Problem(
        ports=ports,
        services=services,
        demands=demands
    )


# -------------------------------------------------
# Full pipeline test
# -------------------------------------------------
def test_full_optimization():

    start_total = time.time()

    print("\n" + "=" * 70)
    print("LINER SHIPPING OPTIMIZATION TEST")
    print("=" * 70)

    # -------------------------------------------------
    # Choose dataset
    # -------------------------------------------------
    dataset = "data/large_shipping_problem.json"
    # dataset = "data/sample_problem.json"

    print("\n1️⃣ Loading dataset...")

    problem = load_problem(dataset)

    print(f"Ports: {len(problem.ports)}")
    print(f"Services: {len(problem.services)}")
    print(f"Demand lanes: {len(problem.demands)}")

    total_demand = sum(d.weekly_teu for d in problem.demands)

    print(f"Total weekly demand: {total_demand:,.0f} TEU")

    # -------------------------------------------------
    # Run Genetic Algorithm
    # -------------------------------------------------
    print("\n2️⃣ Running Genetic Algorithm")

    start_ga = time.time()

    ga = SimpleGA(problem)

    best_chromosome = ga.run()

    ga_time = time.time() - start_ga

    selected_services = sum(best_chromosome.services)

    print("\nGA RESULT")
    print("-" * 40)
    print(f"Selected services: {selected_services}")
    print(f"Estimated fitness: ${best_chromosome.fitness:,.0f}")
    print(f"GA runtime: {ga_time:.2f} seconds")

    if selected_services == 0:
        print("⚠ GA selected no services — stopping pipeline")
        return

    # -------------------------------------------------
    # Run MILP Optimization
    # -------------------------------------------------
    print("\n3️⃣ Running MILP Cargo Flow Optimization")

    start_milp = time.time()

    milp = SimpleMilp(problem, best_chromosome)

    result = milp.solve()

    milp_time = time.time() - start_milp

    # -------------------------------------------------
    # Print Results
    # -------------------------------------------------
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    print(f"Status: {result['status']}")

    if result["status"] == "optimal":

        print(f"Weekly Profit: ${result['profit']:,.0f}")
        print(f"Demand Coverage: {result['coverage']:.2f}%")
        print(f"Services Used: {result['num_services']}")
        print(f"Operational Cost: ${result['cost']:,.0f}")
        print(f"Satisfied Demand: {result['satisfied_demand']:,.0f} TEU")

    print("\nPerformance")
    print("-" * 40)
    print(f"GA Runtime: {ga_time:.2f} sec")
    print(f"MILP Runtime: {milp_time:.2f} sec")

    total_time = time.time() - start_total

    print(f"Total Pipeline Time: {total_time:.2f} sec")

    print("=" * 70)

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------
    if result["status"] == "optimal" and result["profit"] > 0:

        print("\n✅ Optimization pipeline working correctly!")

    else:

        print("\n⚠ Optimization finished but solution may be weak.")


# -------------------------------------------------
# Main
# -------------------------------------------------
if __name__ == "__main__":
    test_full_optimization()