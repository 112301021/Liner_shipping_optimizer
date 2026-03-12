import pandas as pd
from pathlib import Path
from src.optimization.data import Port
from src.optimization.data import Demand

class NetworkLoader:

    
    def __init__(self, data_dir="data"):

        base = Path(__file__).resolve().parents[2]
        self.data_dir = base / "data" / "raw"

    # --------------------------------
    # Load ports
    # --------------------------------
    def load_ports(self):

        ports_file = self.data_dir / "ports.csv"

        df = pd.read_csv(ports_file, sep="\t")
        df.columns = [c.strip().lower() for c in df.columns]

        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

        df = df.dropna(subset=["latitude", "longitude"])

        ports = []

        for _, row in df.iterrows():

            ports.append(
                Port(
                    id=str(row["unlocode"]).strip(),
                    name=str(row["name"]).strip(),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"])
                )
            )

        return ports

    # --------------------------------
    # Load demand
    # --------------------------------
    def load_demands(self):

        demand_file = self.data_dir / "Demand_WorldLarge.csv"

        df = pd.read_csv(demand_file, sep="\t")
        df.columns = [c.strip() for c in df.columns]

        demands = []

        for _, row in df.iterrows():

            origin = str(row["Origin"]).strip()
            dest = str(row["Destination"]).strip()

            if origin == dest:
                continue

            demands.append(
                Demand(
                    origin=origin,
                    destination=dest,
                    weekly_teu=float(row["FFEPerWeek"]),
                    revenue_per_teu=float(row["Revenue_1"])
                )
            )

        return demands

    # --------------------------------
    # Load distance matrix
    # --------------------------------
    def load_distance_matrix(self):

        dist_file = self.data_dir / "dist_dense.csv"

        df = pd.read_csv(dist_file, sep="\t")
        df.columns = [c.strip().lower() for c in df.columns]

        matrix = {}

        for _, row in df.iterrows():

            o = str(row["fromunlocode"]).strip()
            d = str(row["tounlocode"]).strip()
            dist = float(row["distance"])

            matrix.setdefault(o, {})
            matrix[o][d] = dist

        return matrix

    # --------------------------------
    # MAIN LOADER
    # --------------------------------
    def load_network(self):

        ports = self.load_ports()
        demands = self.load_demands()
        distance_matrix = self.load_distance_matrix()

        port_ids = {p.id for p in ports}

        # ensure every port exists in matrix
        for pid in port_ids:
            distance_matrix.setdefault(pid, {})

        return {
            "ports": ports,
            "demands": demands,
            "distance_matrix": distance_matrix
        }
   
