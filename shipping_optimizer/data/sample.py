import json
import sys
from pathlib import Path
# Add parent directory to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.optimization.data import Port, Service, Demand, Problem
def create_sample_problem() -> Problem:
    """Create sample problem"""
    # 10 major ports
    ports = [
        Port(0, "Shanghai", 31.2, 121.5, 150),
        Port(1, "Singapore", 1.3, 103.8, 120),
        Port(2, "Rotterdam", 51.9, 4.5, 180),
        Port(3, "Los Angeles", 33.7, -118.2, 200),
        Port(4, "Hamburg", 53.5, 9.9, 170),
        Port(5, "Hong Kong", 22.3, 114.2, 140),
        Port(6, "Dubai", 25.3, 55.3, 130),
        Port(7, "Tokyo", 35.7, 139.8, 190),
        Port(8, "New York", 40.7, -74.0, 210),
        Port(9, "Mumbai", 19.1, 72.9, 110),
    ]
    # 15 possible services
    services = [
        Service(0, [0, 1, 2], 5000, 150000, 14),  # Asia-Europe mainline
        Service(1, [0, 3], 6000, 180000, 10),     # Trans-Pacific
        Service(2, [1, 6, 2], 4000, 120000, 16),  # Asia-ME-Europe
        Service(3, [5, 7, 0], 3000, 80000, 7),    # Intra-Asia
        Service(4, [2, 4, 8], 5500, 140000, 12),  # Europe-US
        Service(5, [0, 1, 5], 4500, 100000, 8),   # Asia loop
        Service(6, [1, 9, 6], 3500, 90000, 14),   # Asia-India-ME
        Service(7, [3, 8], 7000, 200000, 9),      # US coastal
        Service(8, [2, 4], 4000, 70000, 5),       # Europe loop
        Service(9, [0, 7, 3], 6000, 170000, 12),  # Asia-US Pacific
        Service(10, [1, 2, 4], 5000, 130000, 15), # Singapore-Europe
        Service(11, [5, 1, 9], 4000, 95000, 10),  # HK-Singapore-India
        Service(12, [6, 2, 8], 4500, 110000, 17), # ME-Europe-US
        Service(13, [0, 5, 7], 3500, 75000, 6),   # East Asia
        Service(14, [1, 6, 9], 3000, 85000, 13),  # South route
    ]
    # 30 major demand lanes
    demands = [
        Demand(0, 2, 10000, 1200),  # Shanghai-Rotterdam
        Demand(0, 3, 8000, 1400),   # Shanghai-LA
        Demand(1, 2, 7000, 1100),   # Singapore-Rotterdam
        Demand(0, 8, 5000, 1500),   # Shanghai-NY
        Demand(5, 3, 6000, 1300),   # HK-LA
        Demand(1, 4, 4000, 1000),   # Singapore-Hamburg
        Demand(7, 3, 5500, 1350),   # Tokyo-LA
        Demand(0, 4, 4500, 1150),   # Shanghai-Hamburg
        Demand(1, 9, 3000, 900),    # Singapore-Mumbai
        Demand(6, 2, 3500, 1050),   # Dubai-Rotterdam
        Demand(5, 2, 4000, 1100),   # HK-Rotterdam
        Demand(0, 6, 3000, 950),    # Shanghai-Dubai
        Demand(1, 8, 2500, 1250),   # Singapore-NY
        Demand(7, 8, 3500, 1400),   # Tokyo-NY
        Demand(2, 3, 2000, 1300),   # Rotterdam-LA
        Demand(4, 8, 1800, 1100),   # Hamburg-NY
        Demand(5, 9, 2200, 850),    # HK-Mumbai
        Demand(0, 9, 2800, 880),    # Shanghai-Mumbai
        Demand(1, 6, 2600, 920),    # Singapore-Dubai
        Demand(7, 1, 3200, 1050),   # Tokyo-Singapore
        Demand(3, 8, 2900, 1350),   # LA-NY
        Demand(2, 8, 1500, 1200),   # Rotterdam-NY
        Demand(5, 6, 1700, 900),    # HK-Dubai
        Demand(0, 1, 5000, 800),    # Shanghai-Singapore
        Demand(6, 9, 1600, 750),    # Dubai-Mumbai
        Demand(4, 2, 1400, 950),    # Hamburg-Rotterdam
        Demand(7, 5, 2100, 880),    # Tokyo-HK
        Demand(3, 2, 1900, 1400),   # LA-Rotterdam
        Demand(1, 3, 2400, 1300),   # Singapore-LA
        Demand(5, 4, 1800, 1050),   # HK-Hamburg
    ]
    return Problem(ports=ports, services=services, demands=demands)
def save_json(problem: Problem, filename: str):
    """Save problem to JSON file"""
    data = {
        "ports": [
            {
                "id": p.id,
                "name": p.name,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "handling_cost": p.handling_cost
            }
            for p in problem.ports
        ],
        "services": [
            {
                "id": s.id,
                "ports": s.ports,
                "capacity": s.capacity,
                "weekly_cost": s.weekly_cost,
                "cycle_time": s.cycle_time
            }
            for s in problem.services
        ],
        "demands": [
            {
                "origin": d.origin,
                "destination": d.destination,
                "weekly_teu": d.weekly_teu,
                "revenue_per_teu": d.revenue_per_teu
            }
            for d in problem.demands
        ]
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
if __name__ == "__main__":
    print("Creating sample problem...")
    problem = create_sample_problem()
    output_file = "data/sample_problem.json"
    save_json(problem, output_file)
    print(f"✓ Saved to {output_file}")
    print(f"  Ports: {len(problem.ports)}")
    print(f"  Services: {len(problem.services)}")
    print(f"  Demands: {len(problem.demands)}")
    print(f"  Total demand: {sum(d.weekly_teu for d in problem.demands):,} TEU/week")
