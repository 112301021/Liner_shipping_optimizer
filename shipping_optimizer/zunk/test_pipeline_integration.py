"""
Simple test to check if the pipeline integrates with the dashboard
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent)
sys.path.insert(0, parent_dir)

def test_pipeline():
    """Run the orchestrator and return results"""
    print("Running test orchestrator...")

    # Import test orchestrator
    from tests.test_orchestrator import test_orchestrator

    # Run the test
    result = test_orchestrator()

    # Save results for dashboard
    output_file = parent_dir + "/pipeline_output.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to {output_file}")

    # Print key metrics
    metrics = result.get("summary_metrics", {})
    print(f"\nKey Metrics:")
    print(f"  Weekly Profit: ${metrics.get('weekly_profit', 0):,.0f}")
    print(f"  Annual Profit: ${metrics.get('annual_profit', 0):,.0f}")
    print(f"  Coverage: {metrics.get('coverage', 0):.1f}%")
    print(f"  Services: {metrics.get('total_services', 0)}")

    return result

if __name__ == "__main__":
    test_pipeline()