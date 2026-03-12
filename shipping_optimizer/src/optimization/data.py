from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Port:
    id: int
    name: str
    latitude: float
    longitude: float
    handling_cost: float = 0
    draft: float = 0
    port_call_cost: float = 0


@dataclass
class Service:
    id: int
    ports: List[int]
    capacity: float
    weekly_cost: float
    cycle_time: int = 7
    speed: float = 18
    fuel_cost: float = 0


@dataclass
class Demand:
    origin: int
    destination: int
    weekly_teu: float
    revenue_per_teu: float


class Problem:

    def __init__(
        self,
        ports: List[Port],
        services: List[Service],
        demands: List[Demand],
        distance_matrix: Dict = None
    ):
        self.ports = ports
        self.services = services
        self.demands = demands
        self.distance_matrix = distance_matrix 

        if self.distance_matrix is None:
            raise ValueError("Problem must include distance_matrix")