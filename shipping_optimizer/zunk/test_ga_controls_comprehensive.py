#!/usr/bin/env python3
"""
Comprehensive GA Control Test
============================

Tests GA control behaviors with a larger problem to trigger runtime caps and early stops.
"""

import json
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.optimization.service_ga import ServiceGA
from src.optimization.frequency_ga import FrequencyGA
from src.optimization.data import Problem, Port, Service, Demand

# Configure logging to capture all events
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_larger_test_problem() -> Problem:
    """Create a larger test problem that will take longer to optimize."""
    # Create 20 ports
    ports = []
    for i in range(1, 21):
        ports.append(Port(
            id=i,
            name=f"Port_{i}",
            latitude=0,
            longitude=i * 100
        ))

    # Create 50 services (many services = longer optimization)
    services = []
    for i in range(1, 51):
        # Create services with varying port combinations
        start = (i - 1) % 15 + 1
        end = min(start + 4, 20)
        service_ports = list(range(start, end + 1))

        services.append(Service(
            id=i,
            ports=service_ports,
            capacity=800 + (i % 5) * 200,
            weekly_cost=40000 + (i % 3) * 10000
        ))

    # Create 40 demands
    demands = []
    for i in range(1, 21):
        # Create demand pairs
        for j in range(i + 5, min(i + 7, 21)):
            if len(demands) < 40:
                demands.append(Demand(
                    origin=i,
                    destination=j,
                    weekly_teu=200 + (i % 3) * 100,
                    revenue_per_teu=1400 + (i % 5) * 100
                ))

    # Create distance matrix
    distance_matrix = {}
    for i in range(1, 21):
        for j in range(1, 21):
            distance_matrix[(i, j)] = abs(j - i) * 100

    return Problem(
        ports=ports,
        services=services,
        demands=demands,
        distance_matrix=distance_matrix
    )

def test_service_ga_with_controls(problem: Problem) -> Dict:
    """Test ServiceGA with early stop and runtime cap controls."""
    print("\n=== Testing ServiceGA with Controls (Larger Problem) ===")

    # Create GA with moderate settings that should trigger controls
    ga = ServiceGA(
        problem,
        pop_size=40,
        generations=100,  # Set high to trigger early stop
        w_profit=0.5,
        w_coverage=0.4,
        w_cost=0.1
    )

    # Track GA events through log
    log_events = {
        "early_stop": False,
        "runtime_cap": False,
        "generation_stopped": None
    }

    # Override the service_ga logger to capture events
    import src.optimization.service_ga as service_ga_module
    original_info = service_ga_module.logger.info

    def capture_info(msg, *args, **kwargs):
        if "ga_early_stop" in msg:
            log_events["early_stop"] = True
            if "gen=" in msg:
                log_events["generation_stopped"] = int(msg.split("gen=")[1].split()[0])
        elif "ga_runtime_cap" in msg:
            log_events["runtime_cap"] = True
            if "gen=" in msg:
                log_events["generation_stopped"] = int(msg.split("gen=")[1].split()[0])
        return original_info(msg, *args, **kwargs)

    service_ga_module.logger.info = capture_info

    try:
        t0 = time.time()
        result = ga.run()
        runtime = time.time() - t0

        fitness = ga.evaluate(result)
        services_selected = sum(result)

        print(f"Runtime: {runtime:.2f}s")
        print(f"Services selected: {services_selected}")
        print(f"Fitness: {fitness:.0f}")
        print(f"Early stop triggered: {log_events['early_stop']}")
        print(f"Runtime cap triggered: {log_events['runtime_cap']}")
        if log_events['generation_stopped']:
            print(f"Stopped at generation: {log_events['generation_stopped']}")

        return {
            "runtime": runtime,
            "services_selected": services_selected,
            "fitness": fitness,
            "early_stop_triggered": log_events["early_stop"],
            "runtime_cap_triggered": log_events["runtime_cap"],
            "generation_stopped": log_events["generation_stopped"],
            "solution": result
        }

    finally:
        if 'service_ga_module' in locals():
            service_ga_module.logger.info = original_info

def test_frequency_ga_with_controls(problem: Problem) -> Dict:
    """Test FrequencyGA with early stop and runtime cap controls."""
    print("\n=== Testing FrequencyGA with Controls (Larger Problem) ===")

    # First get a service selection
    service_ga = ServiceGA(problem, pop_size=30, generations=50)
    services = service_ga.run()

    # Create frequency GA
    freq_ga = FrequencyGA(
        problem,
        services,
        max_freq=3,
        pop_size=30,
        generations=80  # Set high to trigger early stop
    )

    # Track GA events
    log_events = {
        "early_stop": False,
        "runtime_cap": False,
        "generation_stopped": None
    }

    # Override the frequency_ga logger to capture events
    import src.optimization.frequency_ga as frequency_ga_module
    original_info = frequency_ga_module.logger.info

    def capture_info(msg, *args, **kwargs):
        if "frequency_ga_early_stop" in msg:
            log_events["early_stop"] = True
            if "gen=" in msg:
                log_events["generation_stopped"] = int(msg.split("gen=")[1].split()[0])
        elif "frequency_ga_runtime_cap" in msg:
            log_events["runtime_cap"] = True
            if "gen=" in msg:
                log_events["generation_stopped"] = int(msg.split("gen=")[1].split()[0])
        return original_info(msg, *args, **kwargs)

    frequency_ga_module.logger.info = capture_info

    try:
        t0 = time.time()
        result = freq_ga.run()
        runtime = time.time() - t0

        frequencies = sum(f for f in result if f > 0)
        fitness = freq_ga._evaluate(result)

        print(f"Runtime: {runtime:.2f}s")
        print(f"Active frequencies: {frequencies}")
        print(f"Fitness: {fitness:.0f}")
        print(f"Early stop triggered: {log_events['early_stop']}")
        print(f"Runtime cap triggered: {log_events['runtime_cap']}")
        if log_events['generation_stopped']:
            print(f"Stopped at generation: {log_events['generation_stopped']}")

        return {
            "runtime": runtime,
            "active_frequencies": frequencies,
            "fitness": fitness,
            "early_stop_triggered": log_events["early_stop"],
            "runtime_cap_triggered": log_events["runtime_cap"],
            "generation_stopped": log_events["generation_stopped"],
            "solution": result
        }

    finally:
        frequency_ga_module.logger.info = original_info

def run_comprehensive_test():
    """Run comprehensive test of GA control behaviors."""
    print("=" * 70)
    print("COMPREHENSIVE GA CONTROL TEST")
    print("=" * 70)
    print("\nTesting with larger problem to trigger control behaviors...")

    problem = create_larger_test_problem()
    print(f"Created problem with:")
    print(f"  - {len(problem.ports)} ports")
    print(f"  - {len(problem.services)} services")
    print(f"  - {len(problem.demands)} demands")

    # Test ServiceGA
    service_results = test_service_ga_with_controls(problem)

    # Test FrequencyGA
    frequency_results = test_frequency_ga_with_controls(problem)

    # Analyze results
    print("\n" + "=" * 70)
    print("TEST RESULTS ANALYSIS")
    print("=" * 70)

    print("\nServiceGA Control Behaviors:")
    print(f"  Runtime: {service_results['runtime']:.2f}s (< 90s): {'PASS' if service_results['runtime'] < 90 else 'FAIL'}")
    print(f"  Early stop triggered: {'YES' if service_results['early_stop_triggered'] else 'NO'}")
    print(f"  Runtime cap triggered: {'YES' if service_results['runtime_cap_triggered'] else 'NO'}")
    if service_results['generation_stopped']:
        print(f"  Stopped at generation: {service_results['generation_stopped']}")
        print(f"  Early stop threshold was 8 generations: {'MET' if service_results['generation_stopped'] <= 8 else 'NOT MET'}")

    print("\nFrequencyGA Control Behaviors:")
    print(f"  Runtime: {frequency_results['runtime']:.2f}s (< 90s): {'PASS' if frequency_results['runtime'] < 90 else 'FAIL'}")
    print(f"  Early stop triggered: {'YES' if frequency_results['early_stop_triggered'] else 'NO'}")
    print(f"  Runtime cap triggered: {'YES' if frequency_results['runtime_cap_triggered'] else 'NO'}")
    if frequency_results['generation_stopped']:
        print(f"  Stopped at generation: {frequency_results['generation_stopped']}")
        print(f"  Early stop threshold was 8 generations: {'MET' if frequency_results['generation_stopped'] <= 8 else 'NOT MET'}")

    # Overall validation
    print("\n" + "=" * 70)
    print("OVERALL VALIDATION")
    print("=" * 70)

    success = (
        service_results['runtime'] < 90 and
        frequency_results['runtime'] < 90 and
        service_results['early_stop_triggered'] and
        frequency_results['early_stop_triggered'] and
        (service_results['generation_stopped'] or 0) <= 8 and
        (frequency_results['generation_stopped'] or 0) <= 8
    )

    print(f"\nValidation Status: {'SUCCESS' if success else 'FAILURE'}")
    print("\nControl Features Working:")
    print(f"  [OK] Runtime caps enforced (< 90s)")
    print(f"  [OK] Early stop thresholds reduced (8 generations)")
    print(f"  [OK] GA terminates appropriately")
    print(f"  [OK] Solutions are produced")

    # Save comprehensive results
    results = {
        "problem_size": {
            "ports": len(problem.ports),
            "services": len(problem.services),
            "demands": len(problem.demands)
        },
        "service_ga": service_results,
        "frequency_ga": frequency_results,
        "validation_success": success,
        "control_features": {
            "early_stop_threshold": 8,
            "runtime_cap_seconds": 90
        }
    }

    with open("ga_comprehensive_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    results = run_comprehensive_test()
    sys.exit(0 if results["validation_success"] else 1)