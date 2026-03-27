"""
Scalable RL Training Script (Production-Ready)

Upgrades:
- Uses ScalablePolicy (not SimplePolicy)
- GPU support
- CLI configurable (no hardcoding)
- Checkpointing (best model)
- Resume training support
- Logging + performance tracking
- Handles large-scale problems
"""

import json
import torch
import argparse
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.optimization.data import Problem, Port, Service, Demand
from src.rl.rl_environment import ServiceSelectionEnv
from src.rl.rl_policy import ScalablePolicy
from src.rl.rl_trainer import PPOTrainer


# ------------------------------------------------
# LOAD PROBLEM
# ------------------------------------------------
def load_problem(filename: str) -> Problem:

    with open(filename) as f:
        data = json.load(f)

    ports = [Port(**p) for p in data["ports"]]
    services = [Service(**s) for s in data["services"]]
    demands = [Demand(**d) for d in data["demands"]]

    return Problem(ports=ports, services=services, demands=demands)


# ------------------------------------------------
# TRAIN FUNCTION
# ------------------------------------------------
def train_rl_model(args):

    print("\n" + "=" * 70)
    print("SCALABLE RL TRAINING")
    print("=" * 70)

    start_time = time.time()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ---- Load Problem ----
    print(f"\n1. Loading problem: {args.problem_file}")
    problem = load_problem(args.problem_file)

    print(f"   ✓ Ports: {len(problem.ports)}")
    print(f"   ✓ Services: {len(problem.services)}")
    print(f"   ✓ Demands: {len(problem.demands)}")

    # ---- Environment ----
    print("\n2. Creating environment...")
    env = ServiceSelectionEnv(
        problem,
        max_services=args.max_services
    )

    obs_dim = env.observation_space.shape[0]
    num_actions = env.action_space.n

    print(f"   ✓ Obs dim: {obs_dim}")
    print(f"   ✓ Actions: {num_actions}")

    # ---- Policy ----
    print("\n3. Creating policy...")

    policy = ScalablePolicy(
        obs_dim,
        num_actions,
        hidden_dim=args.hidden_dim
    ).to(device)

    # Resume training if exists
    if args.resume and Path(args.save_path).exists():
        print("   ✓ Loading existing model (resume training)")
        policy.load_state_dict(torch.load(args.save_path, map_location=device))

    num_params = sum(p.numel() for p in policy.parameters())
    print(f"   ✓ Parameters: {num_params:,}")

    # ---- Trainer ----
    print("\n4. Creating PPO trainer...")

    trainer = PPOTrainer(
        env,
        policy,
        learning_rate=args.lr,
        batch_size=args.batch_size,
        update_epochs=args.update_epochs
    )

    print("   ✓ Trainer ready")

    # ---- Training Loop ----
    print(f"\n5. Training for {args.episodes} episodes...\n")

    rewards = []
    best_reward = -float("inf")

    for episode in range(args.episodes):

        trajectory = trainer.collect_episode()

        episode_reward = sum(t["reward"] for t in trajectory)
        rewards.append(episode_reward)

        returns, advantages = trainer.compute_gae(trajectory)
        trainer.update_policy(trajectory, returns, advantages)

        # ---- Save Best Model ----
        if episode_reward > best_reward:
            best_reward = episode_reward
            torch.save(policy.state_dict(), args.save_path)

        # ---- Logging ----
        if episode % args.log_interval == 0:
            avg = sum(rewards[-10:]) / max(1, len(rewards[-10:]))
            print(f"[Episode {episode}] Reward: {episode_reward:.4f} | Avg(10): {avg:.4f}")

    # ---- Final Save ----
    print(f"\n6. Saving final model to {args.save_path}")
    Path(args.save_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(policy.state_dict(), args.save_path)

    duration = time.time() - start_time

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)

    print(f"\nFinal Avg Reward: {sum(rewards[-10:]) / 10:.4f}")
    print(f"Best Reward: {best_reward:.4f}")
    print(f"Training Time: {duration:.2f} sec")
    print(f"Model saved at: {args.save_path}")


# ------------------------------------------------
# CLI ENTRY
# ------------------------------------------------
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--problem_file", type=str, default="data/sample_problem.json")
    parser.add_argument("--save_path", type=str, default="models/rl_policy.pth")

    parser.add_argument("--episodes", type=int, default=500)
    parser.add_argument("--max_services", type=int, default=20)

    parser.add_argument("--hidden_dim", type=int, default=256)
    parser.add_argument("--lr", type=float, default=3e-4)

    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--update_epochs", type=int, default=4)

    parser.add_argument("--log_interval", type=int, default=10)

    parser.add_argument("--resume", action="store_true")

    args = parser.parse_args()

    train_rl_model(args)