""" 
Test the complete optimization pipeline GA -> MILP -> Results """

import json 
import sys
from pathlib import Path 

sys.path.insert(0,str(Path(__file__).parent.parent))

from src.optimization.data import Problem, Port, Service, Demand 
from src.optimization.simple_ga import SimpleGA
from src.optimization.simple_milp import SimpleMILP 

def load_problem(filename: str) -> Problem:
    """Load problem fromm JSON"""
    with open(filename) as f:
        data = json.load(f)


    ports = [Port(**p) for p in data['ports']]
    services = [Service(**s) for s in data['services']]
    demands = [Demand(**d) for d in data['demands']]

    return Problem(ports=ports,services=services,demands=demands)

def test_full_optimization():
    """Test GA + MILP pipeline"""
    print("\n" + "="*60)
    print("Testing Complete Optimization Pipeline")
    print("="*60)

    print("\n1.Loading problem....")
    problem = load_problem("data/sample_problem.json")
    print(f"   ✓ {len(problem.ports)} ports")
    print(f"   ✓ {len(problem.services)} services")
    print(f"   ✓ {len(problem.demands)} demands")

    #Run GA 
    print("\n2.Running Genetic Algorithm..")
    ga = SimpleGA(problem)
    best_chromosome = ga.run()
    print(f"   ✓ Best solution: {sum(best_chromosome.services)} services")
    print(f"   ✓ Estimated fitness: ${best_chromosome.fitness:,.0f}")

    #Run MILP
    print("\n3. Running MILP optimization...")
    milp = SimpleMILP(problem, best_chromosome)
    result = milp.solve()

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Status: {result['status']}")
    print(f"Profit: ${result['profit']:,.0f} per week")
    print(f"Coverage: {result['converge']:.1f}%")
    print(f"Services: {result['num_services']}")
    print("="*60)

    assert result['status'] == 'optimal'
    assert result['profit'] > 0
    print("\n Complete optimization test passed!")

if __name__ == "__main__":
    test_full_optimization() 
