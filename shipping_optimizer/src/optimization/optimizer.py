"""
Scalable Service Optimizer

Upgrades:
- Persistent RL model (no reload per call)
- Device-aware inference
- Warm-start support for GA
- Confidence-based fallback
- Metrics logging hooks
- Ready for Decision Engine integration
"""

from typing import Dict, Any, Optional
from pathlib import Path
import torch

from src.optimization.data import Problem
from src.optimization.fallback_ga import FallbackGA, Chromosome
from src.utils.logger import logger


class ServiceOptimizer:

    def __init__(
        self,
        use_rl: bool = True,
        rl_model_path: Optional[str] = None,
        fallback_to_ga: bool = True,
        confidence_threshold: float = 0.05
    ):
        self.use_rl = use_rl
        self.fallback_to_ga = fallback_to_ga
        self.confidence_threshold = confidence_threshold

        self.rl_available = False
        self.policy = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if use_rl and rl_model_path:
            self.rl_available = self._load_rl_model(rl_model_path)

        logger.info(
            "optimizer_initialized",
            rl_available=self.rl_available,
            fallback_enabled=fallback_to_ga
        )

    def _load_rl_model(self, model_path: str) -> bool:

        if not Path(model_path).exists():
            logger.warning("rl_model_not_found", path=model_path)
            return False

        try:
            from src.rl.rl_policy import ScalablePolicy

            self.rl_model_path = model_path
            self.policy_class = ScalablePolicy

            logger.info("rl_model_loaded", path=model_path)
            return True

        except Exception as e:
            logger.error("rl_model_load_failed", error=str(e))
            return False

    def optimize(self, problem: Problem) -> Chromosome:

        used_rl = False
        confidence = 0.0

        if self.rl_available and self.use_rl:
            try:
                chromosome, confidence = self._optimize_with_rl(problem)

                if confidence >= self.confidence_threshold:
                    used_rl = True

                    logger.info(
                        "rl_optimization_success",
                        services=sum(chromosome.services),
                        confidence=confidence
                    )

                    return chromosome

                else:
                    raise ValueError("Low RL confidence")

            except Exception as e:
                logger.warning("rl_optimization_failed", error=str(e))

                if not self.fallback_to_ga:
                    raise

        # GA fallback
        chromosome = self._optimize_with_ga(problem)

        logger.info(
            "ga_optimization_success",
            services=sum(chromosome.services)
        )

        return chromosome

    def _initialize_policy(self, obs_dim: int, num_actions: int):

        if self.policy is None:
            self.policy = self.policy_class(obs_dim, num_actions)
            self.policy.load_state_dict(torch.load(self.rl_model_path, map_location=self.device))
            self.policy.eval()

    def _optimize_with_rl(self, problem: Problem):

        from src.rl.rl_environment import ServiceSelectionEnv

        env = ServiceSelectionEnv(problem, max_services=20)

        obs_dim = env.observation_space.shape[0]
        num_actions = len(problem.services)

        self._initialize_policy(obs_dim, num_actions)

        obs, _ = env.reset()
        done = False

        selected_services = []
        action_probs = []

        while not done and len(selected_services) < env.max_services:

            action, log_prob, _ = self.policy.select_action(
                obs,
                selected_services,
                deterministic=True
            )

            action_probs.append(np.exp(log_prob))

            obs, _, done, truncated, _ = env.step(action)
            selected_services.append(action)

            if truncated:
                break

        # Confidence = mean probability of chosen actions
        confidence = float(np.mean(action_probs)) if action_probs else 0.0

        services = [0] * len(problem.services)
        frequencies = [0] * len(problem.services)

        for s_id in selected_services:
            services[s_id] = 1
            frequencies[s_id] = 1

        return Chromosome(services, frequencies), confidence

    def _optimize_with_ga(self, problem: Problem) -> Chromosome:

        ga = FallbackGA(problem)
        Chromosome = ga.solve(warm_start = rl_solution)

        # Future-ready: allow warm start
        return ga.run()