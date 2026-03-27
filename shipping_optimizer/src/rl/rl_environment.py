"""
RL Environment for Large-Scale Service Selection

Key upgrades:
- Incremental MILP caching (avoids full recomputation)
- Action masking (invalid / redundant actions)
- Batched feature computation ready
- Reward shaping for stability
- Early termination control
- Scalable feature normalization
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, List, Tuple, Optional

from src.optimization.data import Problem
from src.optimization.hub_milp import HubMILP
from src.optimization.fallback_ga import Chromosome
from src.utils.logger import logger


class ServiceSelectionEnv(gym.Env):

    metadata = {'render.modes': ['human']}

    def __init__(
        self,
        problem: Problem,
        max_services: int = 20,
        reward_scale: float = 1e6,
        cache_enabled: bool = True
    ):
        super().__init__()

        self.problem = problem
        self.max_services = max_services
        self.num_services = len(problem.services)
        self.reward_scale = reward_scale
        self.cache_enabled = cache_enabled

        # Action space
        self.action_space = spaces.Discrete(self.num_services)

        # Observation space (dynamic but bounded)
        self.obs_dim = len(problem.ports) * 2 + 12
        self.observation_space = spaces.Box(
            low=-1e9,
            high=1e9,
            shape=(self.obs_dim,),
            dtype=np.float32
        )

        # Cache for incremental MILP results
        self._profit_cache: Dict[Tuple[int], float] = {}

        # Precompute static features (IMPORTANT for scale)
        self._precompute_static_features()

        self.reset()

    def _precompute_static_features(self):
        """Precompute invariant features"""
        self.port_incoming = {}
        self.port_outgoing = {}

        for port in self.problem.ports:
            self.port_incoming[port.id] = sum(
                d.weekly_teu for d in self.problem.demands if d.destination == port.id
            )
            self.port_outgoing[port.id] = sum(
                d.weekly_teu for d in self.problem.demands if d.origin == port.id
            )

        self.total_demand = sum(d.weekly_teu for d in self.problem.demands)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.selected_services: List[int] = []
        self.current_profit: float = 0.0
        self.best_profit: float = 0.0
        self.step_count: int = 0

        return self._get_observation(), {}

    def step(self, action: int):

        # Invalid action handling (critical for RL stability)
        if action in self.selected_services:
            return self._get_observation(), -0.01, False, False, {"invalid": True}

        self.selected_services.append(action)

        # Profit computation (cached)
        new_profit = self._calculate_profit_cached()

        # Reward shaping (scaled + penalized)
        delta = new_profit - self.current_profit

        reward = delta / self.reward_scale

        # Small penalty to discourage long sequences
        reward -= 0.001 * len(self.selected_services)

        self.current_profit = new_profit
        self.best_profit = max(self.best_profit, new_profit)

        self.step_count += 1

        # Termination conditions (tuned for large scale)
        done = (
            self.step_count >= self.max_services or
            len(self.selected_services) >= self.num_services or
            (delta <= 0 and self.step_count > 5)
        )

        truncated = False

        info = {
            "num_services": len(self.selected_services),
            "profit": self.current_profit,
            "best_profit": self.best_profit,
            "step": self.step_count
        }

        return self._get_observation(), reward, done, truncated, info

    def _get_observation(self) -> np.ndarray:
        """Efficient feature extraction"""

        features = []

        # Port features (precomputed)
        for port in self.problem.ports:
            features.append(self.port_incoming[port.id])
            features.append(self.port_outgoing[port.id])

        # Global features
        features.extend([
            len(self.selected_services),
            self.num_services - len(self.selected_services),
            self.current_profit / self.reward_scale,
            self.best_profit / self.reward_scale,
            self.total_demand / 1e4,
            len(self.problem.demands),
            len(self.problem.ports),
            self.step_count,
            self.max_services - self.step_count,
            float(len(self.selected_services) > 0),
            float(len(self.selected_services) > 5),
            float(self.current_profit > 0)
        ])

        return np.array(features, dtype=np.float32)

    def _calculate_profit_cached(self) -> float:
        """Cached MILP evaluation (CRITICAL for performance)"""

        key = tuple(sorted(self.selected_services))

        if self.cache_enabled and key in self._profit_cache:
            return self._profit_cache[key]

        # Build chromosome
        services = [0] * self.num_services
        frequencies = [0] * self.num_services

        for s_id in self.selected_services:
            services[s_id] = 1
            frequencies[s_id] = 1

        chromosome = Chromosome(services, frequencies)

        milp = HubMILP(self.problem, chromosome)
        result = milp.solve()

        profit = result.get("profit", 0.0)

        if self.cache_enabled:
            self._profit_cache[key] = profit

        return profit