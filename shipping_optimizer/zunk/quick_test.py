#!/usr/bin/env python3
"""
Quick test to verify JSON output and dashboard integration
"""
import json
from pathlib import Path

# Create sample pipeline output
sample_output = {
    "status": "complete",
    "problem_analysis": "Sample problem analysis for testing dashboard integration.",
    "regional_results": [
        {
            "agent": "RegionalAgent",
            "region": "Asia",
            "status": "complete",
            "services_generated": 150,
            "services_filtered": 100,
            "services_selected": 25,
            "weekly_profit": 1500000,
            "coverage_percent": 65.5,
            "operating_cost": 800000,
            "annual_profit": 78000000,
            "profit_margin_pct": 65.2,
            "profit_per_service": 60000,
            "cost_per_service": 32000,
            "uncovered_teu": 50000,
            "hub_ports": ["SIN", "HKG", "SHA"],
            "strategy": "Hybrid hub-and-spoke with direct services on high-demand corridors",
            "explanation": "Verdict: Good\nStrength: High profit margins on selected services\nWeakness: Moderate coverage leaves room for improvement"
        },
        {
            "agent": "RegionalAgent",
            "region": "Europe",
            "status": "complete",
            "services_generated": 120,
            "services_filtered": 85,
            "services_selected": 20,
            "weekly_profit": 1200000,
            "coverage_percent": 58.3,
            "operating_cost": 750000,
            "annual_profit": 62400000,
            "profit_margin_pct": 61.5,
            "profit_per_service": 60000,
            "cost_per_service": 37500,
            "uncovered_teu": 65000,
            "hub_ports": ["RTM", "HAM", "GVA"],
            "strategy": "Hub-and-spoke centered on Rotterdam and Hamburg",
            "explanation": "Verdict: Moderate\nStrength: Stable hub network\nWeakness: Lower coverage than Asia region"
        },
        {
            "agent": "RegionalAgent",
            "region": "Americas",
            "status": "complete",
            "services_generated": 100,
            "services_filtered": 70,
            "services_selected": 15,
            "weekly_profit": 900000,
            "coverage_percent": 52.1,
            "operating_cost": 600000,
            "annual_profit": 46800000,
            "profit_margin_pct": 60.0,
            "profit_per_service": 60000,
            "cost_per_service": 40000,
            "uncovered_teu": 75000,
            "hub_ports": ["NYC", "LAX", "SFO"],
            "strategy": "Direct services with secondary hub connections",
            "explanation": "Verdict: Moderate\nStrength: Efficient direct routing\nWeakness: Limited transcontinental coverage"
        }
    ],
    "executive_summary": "VERDICT: Good\n\nOVERALL PERFORMANCE:\n- Total weekly profit: $3.6M\n- Global coverage: 58.6%\n- Services deployed: 60\n- Annual profit projection: $187.2M\n\nSTRENGTHS:\n1. Strong profitability with 62.8% average margin\n2. Well-diversified regional presence\n3. Efficient hub utilization\n\nWEAKNESSES:\n1. Coverage below 60% threshold\n2. Americas region underperforming\n\nRECOMMENDATIONS:\n1. Priority: Expand coverage in Americas region\n2. Action: Add 5-8 services to under-served corridors",
    "summary_metrics": {
        "weekly_profit": 3600000,
        "annual_profit": 187200000,
        "cost": 2150000,
        "coverage": 58.6,
        "total_services": 60
    },
    "iterations_run": 1,
    "decision_output": {
        "feedback": {
            "convergence_score": 0.75,
            "needs_rerun": False,
            "coverage_gap": 2.5,
            "profit_gap": 150000,
            "conflict_severity": 0
        }
    },
    "iteration_audit": [
        {
            "iteration": 1,
            "profit": 3600000,
            "coverage": 58.6,
            "convergence_score": 0.75,
            "needs_rerun": False,
            "rerun_reason": "",
            "weights_used": {"profit_weight": 0.5, "coverage_weight": 0.3, "cost_weight": 0.2}
        }
    ]
}

# Save the sample output
output_dir = Path.cwd()
output_file = output_dir / "pipeline_output.json"

try:
    with open(output_file, 'w') as f:
        json.dump(sample_output, f, indent=2)
    print(f"[SUCCESS] Sample pipeline output saved to: {output_file}")
    print(f"[SUCCESS] File size: {output_file.stat().st_size} bytes")

    # Verify the file can be read back
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    print(f"[SUCCESS] Verification: Loaded {len(loaded)} top-level keys")
    print(f"[SUCCESS] Regional results: {len(loaded.get('regional_results', []))} regions")

except Exception as e:
    print(f"[ERROR] {e}")