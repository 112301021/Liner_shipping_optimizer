#!/usr/bin/env python3
"""
Step 1 Validation Script for GA Control Fixes
============================================

This script runs the pipeline with modified GA settings to validate:
1. ServiceGA early stop behavior (threshold reduced to 8)
2. FrequencyGA early stop behavior (threshold reduced to 8)
3. Runtime cap enforcement (90 seconds)
4. Output consistency (profit, coverage, services must remain identical)

Usage:
    python validate_step1.py
"""

import json
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.network_loader import NetworkLoader
from src.agents.orchestrator_agent import OrchestratorAgent
from src.optimization.data import Problem, Port, Service, Demand

# Configure logging to capture GA early stops and runtime caps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('step1_validation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Step1Validator:
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.test_data_file = "data/datasets/large_shipping_problem.json"
        self.metrics = {
            "service_ga": {
                "early_stops": 0,
                "runtime_caps": 0,
                "total_runs": 0
            },
            "frequency_ga": {
                "early_stops": 0,
                "runtime_caps": 0,
                "total_runs": 0
            },
            "baseline": None,
            "optimized": None
        }

    def load_problem(self) -> Problem:
        """Load the test problem dataset."""
        logger.info(f"Loading problem from {self.test_data_file}")
        with open(self.test_data_file) as f:
            data = json.load(f)

        ports = [Port(**p) for p in data["ports"]]
        services = [Service(**s) for s in data["services"]]
        demands = [Demand(**d) for d in data["demands"]]

        # Scale demand as done in tests
        DEMAND_SCALE = 6
        for d in demands:
            d.weekly_teu *= DEMAND_SCALE

        loader = NetworkLoader()
        distance_matrix = loader.load_distance_matrix()

        return Problem(
            ports=ports,
            services=services,
            demands=demands,
            distance_matrix=distance_matrix,
        )

    def extract_key_metrics(self, result: Dict) -> Dict:
        """Extract key metrics for comparison."""
        metrics = result["summary_metrics"]

        return {
            "weekly_profit": float(metrics["weekly_profit"]),
            "annual_profit": float(metrics["annual_profit"]),
            "coverage": float(metrics["coverage"]),
            "total_services": metrics["total_services"],
            "cost": float(metrics.get("cost", metrics.get("total_cost", 0))),
            "iterations_run": result.get("iterations_run", 1)
        }

    def run_baseline(self) -> Dict:
        """Run with original settings to establish baseline."""
        logger.info("=== RUNNING BASELINE (Original GA Settings) ===")

        # Temporarily modify GA settings to original values
        import src.optimization.service_ga as service_ga
        import src.optimization.frequency_ga as frequency_ga

        # Store original settings
        orig_service_no_improve = service_ga.NO_IMPROVE_LIMIT
        orig_service_runtime = service_ga.MAX_RUNTIME
        orig_freq_no_improve = frequency_ga.NO_IMPROVE_LIMIT
        orig_freq_runtime = frequency_ga.MAX_RUNTIME

        # Set to original values
        service_ga.NO_IMPROVE_LIMIT = 20  # Original threshold
        service_ga.MAX_RUNTIME = 300     # 5 minutes
        frequency_ga.NO_IMPROVE_LIMIT = 20
        frequency_ga.MAX_RUNTIME = 300

        try:
            problem = self.load_problem()
            t0 = time.perf_counter()
            result = self.orchestrator.process({"problem": problem})
            elapsed = time.perf_counter() - t0

            self.metrics["baseline"] = {
                **self.extract_key_metrics(result),
                "runtime": elapsed
            }

            logger.info(f"Baseline complete in {elapsed:.1f}s")
            logger.info(f"Baseline metrics: {self.metrics['baseline']}")

            return result

        finally:
            # Restore settings
            service_ga.NO_IMPROVE_LIMIT = orig_service_no_improve
            service_ga.MAX_RUNTIME = orig_service_runtime
            frequency_ga.NO_IMPROVE_LIMIT = orig_freq_no_improve
            frequency_ga.MAX_RUNTIME = orig_freq_runtime

    def run_optimized(self) -> Dict:
        """Run with optimized settings (Step 1 fixes)."""
        logger.info("=== RUNNING OPTIMIZED (Step 1 GA Controls) ===")

        problem = self.load_problem()
        t0 = time.perf_counter()
        result = self.orchestrator.process({"problem": problem})
        elapsed = time.perf_counter() - t0

        self.metrics["optimized"] = {
            **self.extract_key_metrics(result),
            "runtime": elapsed
        }

        logger.info(f"Optimized run complete in {elapsed:.1f}s")
        logger.info(f"Optimized metrics: {self.metrics['optimized']}")

        return result

    def compare_metrics(self) -> Dict[str, Any]:
        """Compare baseline and optimized metrics."""
        if not self.metrics["baseline"] or not self.metrics["optimized"]:
            return {"error": "Missing baseline or optimized metrics"}

        baseline = self.metrics["baseline"]
        optimized = self.metrics["optimized"]

        # Calculate differences
        profit_diff = optimized["weekly_profit"] - baseline["weekly_profit"]
        coverage_diff = optimized["coverage"] - baseline["coverage"]
        services_diff = optimized["total_services"] - baseline["total_services"]
        runtime_improvement = (baseline["runtime"] - optimized["runtime"]) / baseline["runtime"] * 100

        # Check consistency (should be identical)
        profit_consistent = abs(profit_diff) / baseline["weekly_profit"] < 0.001  # < 0.1% difference
        coverage_consistent = abs(coverage_diff) < 0.1  # < 0.1 percentage points
        services_consistent = services_diff == 0  # Exact match

        return {
            "profit_difference": profit_diff,
            "profit_consistent": profit_consistent,
            "coverage_difference": coverage_diff,
            "coverage_consistent": coverage_consistent,
            "services_difference": services_diff,
            "services_consistent": services_consistent,
            "runtime_improvement_pct": runtime_improvement,
            "baseline_runtime": baseline["runtime"],
            "optimized_runtime": optimized["runtime"]
        }

    def parse_log_for_ga_events(self, log_file: str = "step1_validation.log") -> Dict:
        """Parse log file for GA early stop and runtime cap events."""
        ga_events = {
            "service_ga": {"early_stops": 0, "runtime_caps": 0},
            "frequency_ga": {"early_stops": 0, "runtime_caps": 0}
        }

        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()

            for line in lines:
                if "ga_early_stop" in line.lower():
                    if "service_ga" in line:
                        ga_events["service_ga"]["early_stops"] += 1
                    elif "frequency_ga" in line:
                        ga_events["frequency_ga"]["early_stops"] += 1

                elif "runtime_cap" in line.lower():
                    if "service_ga" in line:
                        ga_events["service_ga"]["runtime_caps"] += 1
                    elif "frequency_ga" in line:
                        ga_events["frequency_ga"]["runtime_caps"] += 1

        except FileNotFoundError:
            logger.warning(f"Log file {log_file} not found")

        return ga_events

    def run_validation(self) -> Dict:
        """Run complete validation suite."""
        logger.info("Starting Step 1 Validation for GA Control Fixes")
        logger.info("=" * 60)

        # Run baseline with original settings
        self.run_baseline()

        # Run optimized with Step 1 fixes
        self.run_optimized()

        # Compare metrics
        comparison = self.compare_metrics()

        # Parse logs for GA events
        ga_events = self.parse_log_for_ga_events()

        # Prepare final report
        report = {
            "validation_status": "SUCCESS" if comparison.get("profit_consistent") and comparison.get("coverage_consistent") and comparison.get("services_consistent") else "FAILURE",
            "metrics_comparison": comparison,
            "ga_events": ga_events,
            "summary": {
                "outputs_identical": comparison.get("profit_consistent") and comparison.get("coverage_consistent") and comparison.get("services_consistent"),
                "runtime_improved": comparison.get("runtime_improvement_pct", 0) > 0,
                "runtime_improvement_pct": comparison.get("runtime_improvement_pct", 0),
                "early_stops_detected": sum(v["early_stops"] for v in ga_events.values()) > 0,
                "runtime_caps_detected": sum(v["runtime_caps"] for v in ga_events.values()) > 0
            }
        }

        # Save report
        with open("step1_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)

        return report

    def print_report(self, report: Dict):
        """Print formatted validation report."""
        print("\n" + "=" * 70)
        print("STEP 1 VALIDATION REPORT")
        print("=" * 70)

        print(f"\nStatus: {report['validation_status']}")

        comp = report["metrics_comparison"]
        print("\n--- Metric Comparison ---")
        print(f"Weekly Profit:   ${comp.get('baseline', {}).get('weekly_profit', 0):,.0f} → ${comp.get('optimized', {}).get('weekly_profit', 0):,.0f}")
        print(f"                Difference: ${comp.get('profit_difference', 0):,.0f}")
        print(f"                Consistent: {'✓' if comp.get('profit_consistent') else '✗'}")

        print(f"\nCoverage:        {comp.get('baseline', {}).get('coverage', 0):.1f}% → {comp.get('optimized', {}).get('coverage', 0):.1f}%")
        print(f"                Difference: {comp.get('coverage_difference', 0):.1f}pp")
        print(f"                Consistent: {'✓' if comp.get('coverage_consistent') else '✗'}")

        print(f"\nServices:        {comp.get('baseline', {}).get('total_services', 0)} → {comp.get('optimized', {}).get('total_services', 0)}")
        print(f"                Difference: {comp.get('services_difference', 0)}")
        print(f"                Consistent: {'✓' if comp.get('services_consistent') else '✗'}")

        print(f"\nRuntime:         {comp.get('baseline_runtime', 0):.1f}s → {comp.get('optimized_runtime', 0):.1f}s")
        print(f"                Improvement: {comp.get('runtime_improvement_pct', 0):.1f}%")

        print("\n--- GA Event Summary ---")
        events = report["ga_events"]
        print(f"ServiceGA early stops: {events['service_ga']['early_stops']}")
        print(f"ServiceGA runtime caps: {events['service_ga']['runtime_caps']}")
        print(f"FrequencyGA early stops: {events['frequency_ga']['early_stops']}")
        print(f"FrequencyGA runtime caps: {events['frequency_ga']['runtime_caps']}")

        print("\n--- Validation Summary ---")
        summary = report["summary"]
        print(f"Outputs remain identical: {'✓' if summary['outputs_identical'] else '✗'}")
        print(f"Runtime improved: {'✓' if summary['runtime_improved'] else '✗'}")
        print(f"Early stop behavior detected: {'✓' if summary['early_stops_detected'] else '✗'}")
        print(f"Runtime cap behavior detected: {'✓' if summary['runtime_caps_detected'] else '✗'}")

        print("\n" + "=" * 70)


if __name__ == "__main__":
    validator = Step1Validator()
    report = validator.run_validation()
    validator.print_report(report)

    # Exit with appropriate code
    sys.exit(0 if report["validation_status"] == "SUCCESS" else 1)