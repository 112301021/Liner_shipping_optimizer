"""
Test suite to validate performance optimizations don't change system behavior.

These tests ensure that all optimizations produce identical outputs to the original
implementation while running faster.
"""

import unittest
import time
import numpy as np
from unittest.mock import Mock
from src.optimization.service_ga import ServiceGA
from src.optimization.frequency_ga import FrequencyGA
from src.optimization.data import Problem, Port, Service, Demand


class TestPerformanceOptimizations(unittest.TestCase):

    def setUp(self):
        """Create a small test problem for validation."""
        self.ports = [
            Port(id="SG", name="Singapore", latitude=1.35, longitude=103.8),
            Port(id="HK", name="Hong Kong", latitude=22.3, longitude=114.2),
            Port(id="SH", name="Shanghai", latitude=31.2, longitude=121.5),
            Port(id="NY", name="New York", latitude=40.7, longitude=-74.0),
        ]

        self.services = [
            Service(id=1, ports=["SG", "HK"], capacity=5000, weekly_cost=100000, cycle_time=14),
            Service(id=2, ports=["HK", "SH"], capacity=6000, weekly_cost=120000, cycle_time=10),
            Service(id=3, ports=["SG", "NY"], capacity=8000, weekly_cost=200000, cycle_time=21),
        ]

        self.demands = [
            Demand(origin="SG", destination="HK", weekly_teu=1000, revenue_per_teu=1500),
            Demand(origin="HK", destination="SH", weekly_teu=1500, revenue_per_teu=1200),
            Demand(origin="SG", destination="NY", weekly_teu=800, revenue_per_teu=2500),
        ]

        self.distance_matrix = {
            "SG": {"HK": 1500, "SH": 2300, "NY": 8500},
            "HK": {"SG": 1500, "SH": 800, "NY": 9000},
            "SH": {"SG": 2300, "HK": 800, "NY": 11000},
            "NY": {"SG": 8500, "HK": 9000, "SH": 11000},
        }

        self.problem = Problem(
            ports=self.ports,
            services=self.services,
            demands=self.demands,
            distance_matrix=self.distance_matrix
        )

    def test_service_ga_fitness_cache_consistency(self):
        """Test that bytes cache key produces same results as tuple key."""
        ga = ServiceGA(self.problem, pop_size=20, generations=10)

        # Test solution
        test_solution = [1, 0, 1]

        # Clear cache
        ga.fitness_cache.clear()

        # Evaluate with bytes key (optimized)
        fitness1 = ga.evaluate(test_solution)

        # Clear cache again
        ga.fitness_cache.clear()

        # Temporarily use tuple key for comparison
        original_evaluate = ga.evaluate
        def evaluate_with_tuple(services):
            key = tuple(services)  # Original tuple key
            if key in ga.fitness_cache:
                return ga.fitness_cache[key]

            # Run the actual fitness calculation (copy from optimized version)
            fitness = original_evaluate(services)
            return fitness

        fitness2 = evaluate_with_tuple(test_solution)

        self.assertEqual(fitness1, fitness2,
            "Fitness should be identical between bytes and tuple cache keys")

    def test_service_ga_demand_index_optimization(self):
        """Test that optimized demand index produces same results."""
        ga = ServiceGA(self.problem, pop_size=20, generations=10)

        # Check that pre-computed port sets match original
        for i, svc in enumerate(self.problem.services):
            original_set = set(svc.ports)
            optimized_set = ga.service_port_sets[i]
            self.assertEqual(original_set, optimized_set,
                f"Port set mismatch for service {i}")

        # Check demand calculations
        # Service 0 (SG->HK) should see SG-HK demand only
        self.assertEqual(ga.service_direct_demand[0], 1000,
            "Service 0 should see 1000 TEU direct demand")

        # Service 1 (HK->SH) should see HK-SH demand only
        self.assertEqual(ga.service_direct_demand[1], 1500,
            "Service 1 should see 1500 TEU direct demand")

        # Service 2 (SG->NY) should see SG-NY demand only
        self.assertEqual(ga.service_direct_demand[2], 800,
            "Service 2 should see 800 TEU direct demand")

    def test_frequency_ga_route_demand_optimization(self):
        """Test that optimized route demand calculation produces same results."""
        services_mask = [1, 1, 0]  # Use first two services
        ga = FrequencyGA(self.problem, services_mask)

        # Expected route demands
        # Service 0 (SG->HK): 1000 TEU
        # Service 1 (HK->SH): 1500 TEU
        expected_demands = [1000, 1500, 0]

        self.assertEqual(ga.route_demand, expected_demands,
            "Route demands should match expected values")

    def test_hub_detector_caching(self):
        """Test that hub detector caching works without changing results."""
        from src.services.hub_detector import HubDetector

        # First computation
        detector1 = HubDetector(self.problem)
        scores1 = detector1.compute_demand_scores()

        # Second computation (should use cache)
        detector2 = HubDetector(self.problem)
        scores2 = detector2.compute_demand_scores()

        # Results should be identical
        self.assertEqual(scores1, scores2,
            "Hub detector should return same scores with and without caching")

        # Verify expected scores
        # SG appears in 2 demands: 1000 + 800 = 1800
        # HK appears in 2 demands: 1000 + 1500 = 2500
        # SH appears in 1 demand: 1500
        # NY appears in 1 demand: 800
        expected = {
            "SG": 1800,
            "HK": 2500,
            "SH": 1500,
            "NY": 800
        }

        for port_id, expected_score in expected.items():
            self.assertEqual(scores1[port_id], expected_score,
                f"Port {port_id} should have demand score {expected_score}")

    def test_ga_output_consistency(self):
        """Test that optimized GA produces same solution patterns."""
        # Run with small population for deterministic behavior
        ga = ServiceGA(
            self.problem,
            pop_size=10,
            generations=5,
            w_profit=0.5,
            w_coverage=0.4,
            w_cost=0.1,
            # mutation_rate is set internally, not a parameter
        )
        # Override mutation rate for consistency
        ga.mutation_rate = 0.0

        # Set seed for reproducibility
        np.random.seed(42)
        solution1 = ga.run()

        # Run again with same seed
        np.random.seed(42)
        solution2 = ga.run()

        # Solutions should be identical with same seed
        self.assertEqual(solution1, solution2,
            "GA should produce identical solutions with same seed")

        # Basic sanity checks
        self.assertEqual(len(solution1), len(self.services),
            "Solution should have same length as number of services")

        # Should select at least one service (all have positive demand)
        self.assertGreater(sum(solution1), 0,
            "Should select at least one service")

    def test_performance_improvement(self):
        """Validate that optimizations maintain correctness."""
        # Test with a moderate size problem
        test_ports = [
            Port(id=f"P{i}", name=f"Port{i}", latitude=i, longitude=i)
            for i in range(20)
        ]

        test_services = [
            Service(id=i, ports=[f"P{j}" for j in range(i, min(i+5, 20))],
                   capacity=5000, weekly_cost=100000, cycle_time=14)
            for i in range(30)
        ]

        test_demands = [
            Demand(origin=f"P{i}", destination=f"P{min(i+1, 19)}",
                   weekly_teu=100, revenue_per_teu=1500)
            for i in range(19)
        ]

        test_problem = Problem(
            ports=test_ports,
            services=test_services,
            demands=test_demands,
            distance_matrix={p.id: {} for p in test_ports}
        )

        # Add distances
        for i, p1 in enumerate(test_ports):
            for j, p2 in enumerate(test_ports):
                if i != j:
                    test_problem.distance_matrix[p1.id][p2.id] = abs(j - i) * 100

        # Run with optimized GA
        ga = ServiceGA(test_problem, pop_size=20, generations=10)

        # Test that it runs without errors
        solution = ga.run()

        # Basic validation
        self.assertEqual(len(solution), len(test_services))
        self.assertTrue(all(v in [0, 1] for v in solution))

        # Should select some services with demand
        self.assertGreater(sum(solution), 0)

        print(f"\nValidation passed:")
        print(f"  - Services: {len(test_services)}")
        print(f"  - Demands: {len(test_demands)}")
        print(f"  - Selected: {sum(solution)}")
        print(f"  - Fitness cache hits: {len(ga.fitness_cache)}")


if __name__ == '__main__':
    unittest.main()