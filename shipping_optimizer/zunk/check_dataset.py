#!/usr/bin/env python
import json

# Load both datasets
datasets = ["sample_problem.json", "large_shipping_problem.json"]

for dataset in datasets:
    print(f"\n{dataset}:")
    print("-" * 40)

    with open(f"data/datasets/{dataset}") as f:
        data = json.load(f)

    ports = len(data["ports"])
    services = len(data["services"])
    demands = len(data["demands"])

    print(f"Ports: {ports}")
    print(f"Services: {services}")
    print(f"Demands: {demands}")

    # Calculate demand scaling needed
    total_demand = sum(d["weekly_teu"] for d in data["demands"])
    print(f"Total demand (raw): {total_demand:,.0f} TEU")

    # The test scales by 6
    scaled_demand = total_demand * 6
    print(f"Total demand (scaled): {scaled_demand:,.0f} TEU")