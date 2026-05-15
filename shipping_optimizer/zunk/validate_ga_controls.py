#!/usr/bin/env python3
"""
GA Control Validation - Direct Test
===================================

Tests the GA control fixes without requiring the full pipeline.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_test_problem() -> Problem:
    """Create a minimal test problem for GA testing."""
    # Simple test with 5 ports and 3 services
    ports = [
        Port(id=1, name="Port 1", latitude=0, longitude=0),
        Port(id=2, name="Port 2", latitude=0, longitude=1),
        Port(id=3, name="Port 3", latitude=0, longitude=2),
        Port(id=4, name="Port 4", latitude=0, longitude=3),
        Port(id=5, name="Port 5", latitude=0, longitude=4),
    ]

    services = [
        Service(id=1, ports=[1, 2, 3], capacity=1000, weekly_cost=50000),
        Service(id=2, ports=[2, 3, 4], capacity=1200, weekly_cost=60000),
        Service(id=3, ports=[3, 4, 5], capacity=800, weekly_cost=40000),
    ]

    demands = [
        Demand(origin=1, destination=3, weekly_teu=500, revenue_per_teu=1500),
        Demand(origin=2, destination=4, weekly_teu=400, revenue_per_teu=1600),
        Demand(origin=3, destination=5, weekly_teu=300, revenue_per_teu=1700),
    ]

    # Create a simple distance matrix
    distance_matrix = {}
    for i in range(1, 6):
        for j in range(1, 6):
            distance_matrix[(i, j)] = abs(j - i) * 100

    return Problem(ports=ports, services=services, demands=demands, distance_matrix=distance_matrix)

def test_service_ga():
    """Test ServiceGA with control fixes."""
    print("\n=== Testing ServiceGA Control Fixes ===")

    problem = create_test_problem()

    # Test with current settings (optimized)
    print("\nRunning ServiceGA with optimized settings...")
    ga = ServiceGA(problem, pop_size=20, generations=30)

    t0 = time.time()
    result = ga.run()
    runtime = time.time() - t0

    fitness = ga.evaluate(result)
    services_selected = sum(result)

    print(f"Runtime: {runtime:.2f}s")
    print(f"Services selected: {services_selected}")
    print(f"Fitness: {fitness:.0f}")

    return {
        "runtime": runtime,
        "services_selected": services_selected,
        "fitness": fitness,
        "solution": result
    }

def test_frequency_ga():
    """Test FrequencyGA with control fixes."""
    print("\n=== Testing FrequencyGA Control Fixes ===")

    problem = create_test_problem()

    # First get a service selection
    service_ga = ServiceGA(problem, pop_size=20, generations=30)
    services = service_ga.run()

    # Test with current settings (optimized)
    print("\nRunning FrequencyGA with optimized settings...")
    freq_ga = FrequencyGA(problem, services, max_freq=3, pop_size=20, generations=30)

    t0 = time.time()
    result = freq_ga.run()
    runtime = time.time() - t0

    frequencies = sum(f for f in result if f > 0)
    fitness = freq_ga._evaluate(result)

    print(f"Runtime: {runtime:.2f}s")
    print(f"Active frequencies: {frequencies}")
    print(f"Fitness: {fitness:.0f}")

    return {
        "runtime": runtime,
        "active_frequencies": frequencies,
        "fitness": fitness,
        "solution": result
    }

def validate_ga_controls():
    """Validate GA control behavior."""
    print("=" * 60)
    print("GA CONTROL VALIDATION - STEP 1")
    print("=" * 60)

    # Test ServiceGA
    service_results = test_service_ga()

    # Test FrequencyGA
    frequency_results = test_frequency_ga()

    # Check if controls are working
    print("\n=== VALIDATION SUMMARY ===")

    # ServiceGA controls
    print("\nServiceGA Controls:")
    print(f"  Runtime < 90s: {'PASS' if service_results['runtime'] < 90 else 'FAIL'}")
    print(f"  Runtime: {service_results['runtime']:.2f}s")
    print(f"  Services selected: {service_results['services_selected']}")

    # FrequencyGA controls
    print("\nFrequencyGA Controls:")
    print(f"  Runtime < 90s: {'PASS' if frequency_results['runtime'] < 90 else 'FAIL'}")
    print(f"  Runtime: {frequency_results['runtime']:.2f}s")
    print(f"  Active frequencies: {frequency_results['active_frequencies']}")

    # Overall validation
    success = (
        service_results['runtime'] < 90 and
        frequency_results['runtime'] < 90 and
        service_results['services_selected'] > 0 and
        frequency_results['active_frequencies'] > 0
    )

    print(f"\nValidation Status: {'SUCCESS' if success else 'FAILURE'}")

    # Save results
    results = {
        "service_ga": service_results,
        "frequency_ga": frequency_results,
        "validation_success": success
    }

    with open("ga_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    results = validate_ga_controls()
    sys.exit(0 if results["validation_success"] else 1)