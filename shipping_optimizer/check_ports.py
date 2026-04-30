#!/usr/bin/env python
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Load dataset
with open("data/datasets/large_shipping_problem.json") as f:
    data = json.load(f)

ports = data["ports"]
print(f"Total ports: {len(ports)}")

# Check for missing coordinates
missing_coords = []
invalid_coords = []
valid_coords = []

for p in ports:
    lat = p.get("latitude")
    lon = p.get("longitude")

    if lat is None or lon is None:
        missing_coords.append(p)
    elif isinstance(lat, str) and lat.lower() in ["nan", "null", ""]:
        missing_coords.append(p)
    elif isinstance(lon, str) and lon.lower() in ["nan", "null", ""]:
        missing_coords.append(p)
    else:
        try:
            lat_f = float(lat)
            lon_f = float(lon)
            if abs(lat_f) > 90 or abs(lon_f) > 180:
                invalid_coords.append(p)
            else:
                valid_coords.append(p)
        except (ValueError, TypeError):
            invalid_coords.append(p)

print(f"\nPorts with valid coordinates: {len(valid_coords)}")
print(f"Ports with missing coordinates: {len(missing_coords)}")
print(f"Ports with invalid coordinates: {len(invalid_coords)}")

if missing_coords:
    print("\nFirst 10 ports with missing coordinates:")
    for p in missing_coords[:10]:
        print(f"  ID {p['id']}: {p['name']} - lat={p.get('latitude')}, lon={p.get('longitude')}")

if invalid_coords:
    print("\nFirst 10 ports with invalid coordinates:")
    for p in invalid_coords[:10]:
        print(f"  ID {p['id']}: {p['name']} - lat={p.get('latitude')}, lon={p.get('longitude')}")