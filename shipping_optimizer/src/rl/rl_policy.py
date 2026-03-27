"""
RL Policy Network (Large-Scale Optimized)

Upgrades:
- Layer normalization (stability)
- Dropout (generalization)
- Mask-safe softmax (no NaNs)
- Batched inference ready
- Device-aware (CPU/GPU)
- Entropy-safe action selection
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class ScalablePolicy(nn.Module):

    def __init__(
        self,
        obs_dim: int,
        num_actions: int,
        hidden_dim: int = 256,
        dropout: float = 0.1
    ):
        super().__init__()

        self.obs_dim = obs_dim
        self.num_actions = num_actions

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Feature extractor (deep + normalized)
        self.feature_net = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),

            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),

            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU()
        )

        # Policy head
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_actions)
        )

        # Value head
        self.value_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

        self.to(self.device)

    def forward(self, obs: torch.Tensor, mask: torch.Tensor = None):
        obs = obs.to(self.device)

        features = self.feature_net(obs)
        logits = self.policy_head(features)

        if mask is not None:
            mask = mask.to(self.device)
            logits = logits.masked_fill(mask.bool(), -1e9)

        value = self.value_head(features)

        return logits, value

    def _masked_softmax(self, logits: torch.Tensor):
        """Numerically stable softmax"""
        logits = logits - logits.max(dim=-1, keepdim=True).values
        probs = torch.exp(logits)
        probs = probs / (probs.sum(dim=-1, keepdim=True) + 1e-8)
        return probs

    def select_action(
        self,
        obs: np.ndarray,
        selected_services: list,
        deterministic: bool = False
    ):
        with torch.no_grad():

            obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)

            # Mask
            mask = torch.zeros(1, self.num_actions, device=self.device)
            if selected_services:
                mask[0, selected_services] = 1

            logits, value = self.forward(obs_tensor, mask)

            probs = self._masked_softmax(logits)

            # Safety fallback (all masked edge case)
            if torch.isnan(probs).any() or probs.sum() == 0:
                probs = torch.ones_like(probs) / self.num_actions

            if deterministic:
                action = torch.argmax(probs, dim=-1).item()
                log_prob = torch.log(probs[0, action] + 1e-8)
            else:
                dist = torch.distributions.Categorical(probs)
                action = dist.sample().item()
                log_prob = dist.log_prob(torch.tensor(action, device=self.device))

            return action, log_prob.item(), value.item()

    def batch_select_action(
        self,
        obs_batch: np.ndarray,
        mask_batch: np.ndarray,
        deterministic: bool = False
    ):
        """
        Batch inference (for large-scale rollout acceleration)
        """

        with torch.no_grad():

            obs_tensor = torch.FloatTensor(obs_batch).to(self.device)
            mask_tensor = torch.FloatTensor(mask_batch).to(self.device)

            logits, values = self.forward(obs_tensor, mask_tensor)
            probs = self._masked_softmax(logits)

            if deterministic:
                actions = torch.argmax(probs, dim=-1)
                log_probs = torch.log(
                    probs.gather(1, actions.unsqueeze(1)) + 1e-8
                ).squeeze()
            else:
                dist = torch.distributions.Categorical(probs)
                actions = dist.sample()
                log_probs = dist.log_prob(actions)

            return (
                actions.cpu().numpy(),
                log_probs.cpu().numpy(),
                values.squeeze().cpu().numpy()
            )