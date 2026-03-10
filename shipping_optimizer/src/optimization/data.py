from dataclasses import dataclass
from typing import List

@dataclass
class Port:
    id:int
    name: str
    latitude: float
    longitude:float
    handling_cost: float

@dataclass
class Service:
    id:int
    ports: List[int]
    capacity:int
    weekly_cost: float
    cycle_time : int
    
@dataclass
class Demand:
    origin: int
    destination : int
    weekly_teu : int
    revenue_per_teu: float
    
@dataclass
class Problem:
    ports: List[Port]
    services: List[Service]
    demands: List[Demand]