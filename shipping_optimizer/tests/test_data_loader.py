"""
Test Network Loader
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.network_loader import NetworkLoader


def test_data_loader():

    print("\n" + "="*70)
    print("TESTING DATA LOADER")
    print("="*70)

    loader = NetworkLoader()

    network = loader.load_network()

    ports = network["ports"]
    demands = network["demands"]
    distance_matrix = network["distance_matrix"]

    print(f"\nPorts loaded: {len(ports)}")
    print(f"Demand lanes loaded: {len(demands)}")
    print(f"Distance matrix size: {len(distance_matrix)}")

    assert len(ports) > 50
    assert len(demands) > len(ports)
    assert len(distance_matrix) >= len(ports)

    print("\n✓ Data loader working")


if __name__ == "__main__":
    test_data_loader()