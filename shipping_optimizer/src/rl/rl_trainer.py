"""
Scalable PPO Trainer

Upgrades:
- Batch processing (no per-step loop bottleneck)
- GAE (Generalized Advantage Estimation)
- Mini-batch PPO updates
- GPU support
- Stable normalization
- Better logging hooks
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np

from typing import List, Dict
from src.rl.rl_environment import ServiceSelectionEnv
from src.rl.rl_policy import ScalablePolicy
from src.utils.logger import logger


class PPOTrainer:

    def __init__(
        self,
        env: ServiceSelectionEnv,
        policy: ScalablePolicy,
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        lam: float = 0.95,
        eps_clip: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
        batch_size: int = 64,
        update_epochs: int = 4
    ):
        self.env = env
        self.policy = policy
        self.device = policy.device

        self.optimizer = optim.Adam(policy.parameters(), lr=learning_rate)

        self.gamma = gamma
        self.lam = lam
        self.eps_clip = eps_clip
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.batch_size = batch_size
        self.update_epochs = update_epochs

    def collect_episode(self):

        obs, _ = self.env.reset()
        done = False

        trajectory = []

        while not done:

            action, log_prob, value = self.policy.select_action(
                obs,
                self.env.selected_services,
                deterministic=False
            )

            next_obs, reward, done, truncated, _ = self.env.step(action)

            trajectory.append({
                "obs": obs,
                "action": action,
                "log_prob": log_prob,
                "value": value,
                "reward": reward,
                "done": done
            })

            obs = next_obs

            if truncated:
                break

        return trajectory

    def compute_gae(self, trajectory):

        rewards = [t["reward"] for t in trajectory]
        values = [t["value"] for t in trajectory] + [0]
        dones = [t["done"] for t in trajectory]

        advantages = []
        gae = 0

        for t in reversed(range(len(rewards))):
            delta = rewards[t] + self.gamma * values[t + 1] * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * self.lam * (1 - dones[t]) * gae
            advantages.insert(0, gae)

        returns = np.array(advantages) + np.array(values[:-1])

        advantages = np.array(advantages)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        return returns, advantages

    def update_policy(self, trajectory, returns, advantages):

        obs = torch.FloatTensor([t["obs"] for t in trajectory]).to(self.device)
        actions = torch.LongTensor([t["action"] for t in trajectory]).to(self.device)
        old_log_probs = torch.FloatTensor([t["log_prob"] for t in trajectory]).to(self.device)

        returns = torch.FloatTensor(returns).to(self.device)
        advantages = torch.FloatTensor(advantages).to(self.device)

        dataset_size = len(trajectory)

        for _ in range(self.update_epochs):

            indices = np.random.permutation(dataset_size)

            for start in range(0, dataset_size, self.batch_size):
                end = start + self.batch_size
                batch_idx = indices[start:end]

                b_obs = obs[batch_idx]
                b_actions = actions[batch_idx]
                b_old_log_probs = old_log_probs[batch_idx]
                b_returns = returns[batch_idx]
                b_advantages = advantages[batch_idx]

                logits, values = self.policy(b_obs)

                probs = F.softmax(logits, dim=-1)
                dist = torch.distributions.Categorical(probs)

                new_log_probs = dist.log_prob(b_actions)
                entropy = dist.entropy().mean()

                ratio = torch.exp(new_log_probs - b_old_log_probs)

                surr1 = ratio * b_advantages
                surr2 = torch.clamp(ratio, 1 - self.eps_clip, 1 + self.eps_clip) * b_advantages

                policy_loss = -torch.min(surr1, surr2).mean()
                value_loss = F.mse_loss(values.squeeze(), b_returns)

                loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy

                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
                self.optimizer.step()

    def train(self, num_episodes: int = 500, verbose: bool = True):

        logger.info("ppo_training_started", episodes=num_episodes)

        rewards_log = []

        for episode in range(num_episodes):

            trajectory = self.collect_episode()

            episode_reward = sum(t["reward"] for t in trajectory)
            rewards_log.append(episode_reward)

            returns, advantages = self.compute_gae(trajectory)

            self.update_policy(trajectory, returns, advantages)

            if verbose and episode % 10 == 0:
                avg_reward = np.mean(rewards_log[-10:])
                logger.info(
                    "ppo_episode",
                    episode=episode,
                    reward=episode_reward,
                    avg_reward=avg_reward
                )
                print(
                    f"Episode {episode:4d} | Reward: {episode_reward:8.4f} | Avg(10): {avg_reward:8.4f}"
                )

        logger.info(
            "ppo_training_complete",
            final_avg=np.mean(rewards_log[-10:])
        )

        return rewards_log