# Liner Shipping Network Optimizer

**A distributed maritime optimization platform for large-scale liner shipping network design**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![PuLP](https://img.shields.io/badge/Solver-PuLP%2FCBC-orange.svg)](https://coin-or.github.io/pulp)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](Dockerfile)

---

## Overview

This system solves the **Liner Shipping Network Design Problem (LSNDP)** at industrial scale — a combinatorial optimization challenge involving simultaneous vessel deployment, service route selection, sailing frequency assignment, and multi-commodity cargo flow routing across a global port network.

The platform is built around a **hierarchical decomposition strategy**: a global orchestrator partitions the world network into geographic regions using K-means clustering, independent regional agents solve sub-problems via a Genetic Algorithm + MILP pipeline, and a coordinator agent resolves cross-regional conflicts through an iterative feedback loop.

This project was developed under professor supervision at **IIT Palakkad** as part of research into large-scale distributed optimization for maritime logistics.

---

## Problem Statement

Global liner shipping carriers operate networks of hundreds of ports, thousands of candidate service routes, and tens of thousands of demand corridors. The core decisions — which routes to operate, at what frequency, and how to route cargo (direct vs. hub transshipment) — form a large-scale Mixed-Integer Program that is computationally intractable at full scale.

The **WorldLarge benchmark** instance used here comprises:

| Dimension | Scale |
|-----------|-------|
| Ports     | 435   |
| Demand corridors | 9,600 |
| Candidate services | ~1,200 generated |
| Weekly demand volume | 800,000+ TEU |
| Fleet constraint | ≤ 300 vessels |

The objective is to maximize network profit (revenue minus operating, transshipment, and port costs) while achieving ≥ 70% demand coverage — a multi-objective combinatorial problem with both integer and continuous decision variables.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI + WEBSOCKET LAYER                        │
│         /api/optimize  ·  /ws/stream  ·  /api/results                  │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │ async RealOrchestratorIntegration
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR AGENT                               │
│   LLM Problem Analysis  ·  K-means Decomposition  ·  Iteration Control │
│   Coverage: OrchestratorAgent  ·  MAX_ITERATIONS = 3                   │
└──────────┬──────────────────────────────────────────────────┬──────────┘
           │ RegionalSplitter (zero-duplication demand split)  │
           ▼                                                   ▼
┌──────────────────────┐                          ┌──────────────────────┐
│   REGIONAL AGENT     │   ThreadPoolExecutor     │   REGIONAL AGENT     │
│   (Asia / Cluster 0) │◄────── parallel ────────►│  (Europe / Cluster 1)│
│                      │                          │                      │
│  ServiceGeneratorAgent                          │  ServiceGeneratorAgent│
│  HierarchicalGA                                 │  HierarchicalGA      │
│  ├── ServiceGA                                  │  ├── ServiceGA       │
│  └── FrequencyGA                                │  └── FrequencyGA     │
│  HubMILP (per cluster)                          │  HubMILP (per cluster)│
└──────────┬───────────┘                          └──────────┬───────────┘
           └──────────────────────┬───────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        COORDINATOR AGENT                                │
│   Conflict Detection  ·  Profit-Priority Resolution  ·  Gradient Feedback│
│   weight_adjustments = f(coverage_gap, profit_gap, conflict_severity)  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                    (iterate if needs_rerun and iteration < 3)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      GLOBAL AGGREGATION                                 │
│   Profit  ·  Coverage  ·  Cost Breakdown  ·  Executive Summary (LLM)   │
└─────────────────────────────────────────────────────────────────────────┘
```

![System Architecture Overview](docs/diagrams/system_architecture_overview.svg)

---

## Optimization Pipeline

### Phase 1 — Problem Decomposition

Geographic K-means clustering partitions ports into 3–5 regions (adaptive to port count). The `RegionalSplitter` assigns demands by origin port — zero duplication, with a formal conservation check: `Σ regional_demand == global_demand`.

```
Global Problem (435 ports, 9,600 demands)
    → PortClustering (K-means, n_clusters = 3 or 5)
    → RegionalSplitter (origin-based, zero-duplication)
    → 3–5 regional sub-problems (disjoint demand sets)
```

### Phase 2 — Service Generation

Each `ServiceGeneratorAgent` builds a candidate service pool using four archetypes:

| Archetype | Description | Typical Count |
|-----------|-------------|---------------|
| **Direct** | Top-500 high-demand corridors | ~500 |
| **Hub loops** | Hub port + top spoke ring (21-day cycle) | ~80 |
| **Trunk routes** | Hub-to-hub backbone (10 pairs × 45 hubs) | ~45 |
| **Feeders** | Spoke-to-best-hub (7-day cycle) | ~300 |
| **Heuristic pool** | Algorithmic candidates | 150 |

![GA + MILP Optimization Pipeline](docs/diagrams/ga_milp_optimization_pipeline.svg)

### Phase 3 — Hierarchical Genetic Algorithm

A two-level GA handles the combinatorial service selection problem:

**Level 1 — ServiceGA** (service selection):
- Chromosome: binary mask `[0,1,...,1,0]` over candidate services
- Population: adaptive (60–140 based on service count)
- Fitness: `w_profit·Profit + w_coverage·Coverage − w_cost·Cost − penalties`
- Operators: demand-weighted initialization, elitist selection, one-point crossover, demand-biased mutation

**Level 2 — FrequencyGA** (frequency assignment):
- Decision: integer frequencies `f_i ∈ {1,2,3}` for selected services
- Analytical warm start: `freq_i = ⌈route_demand_i / capacity_i⌉`
- Fleet constraint enforcement: post-GA pruning by demand-per-vessel efficiency

### Phase 4 — Hub MILP (Flow Allocation)

For each hub cluster, a Mixed-Integer Linear Program allocates cargo flows:

```
Maximize:  Revenue(direct_flow + transfer_flow)
         − OperatingCost(fixed)
         − TransshipCost(80 USD/TEU)
         − PortHandlingCost(15 USD/TEU)
         − UnservedPenalty(300 USD/TEU)

Subject to:
  ∀d: direct_flow_d + transfer_flow_d + unserved_d = demand_d.weekly_teu
  ∀s: Σ flow_through_s ≤ capacity_s × freq_s × (7/cycle_time_s)
  ∀p: Σ flow_through_p ≤ port_capacity_p
  Transfer pairs: up to 2000 (demand-volume prioritized)
```

![Coordinator Feedback Loop](docs/diagrams/coordinator_feedback_loop.svg)

### Phase 5 — Coordination & Iteration

The `CoordinatorAgent` detects services selected in multiple regions, resolves conflicts by retaining them in the highest-profit region, and emits gradient feedback signals:

```python
weight_adjustments = {
    "coverage_weight": min(0.70, 0.40 + coverage_gap/100 × 1.5),
    "profit_weight":   max(0.20, 0.50 − coverage_boost + profit_boost),
    "cost_weight":     max(0.05, 0.10 − profit_boost)
}
convergence_score = (coverage_score + profit_score + conflict_score) / 3
```

The loop terminates when `convergence_score → 1.0`, coverage gain < 1pp, or `MAX_ITERATIONS = 3` is reached.

---

## Repository Structure

```
shipping_optimizer/
├── backend/                          # FastAPI + WebSocket orchestration layer
│   ├── main.py                       # API entry point, route registration
│   ├── real_orchestrator_integration.py  # Async pipeline bridge
│   └── pipeline_streamer.py          # WebSocket event broadcaster
│
├── src/                              # Core optimization engine
│   ├── agents/                       # Multi-agent framework
│   │   ├── base.py                   # BaseAgent (LLM wrapper, retry logic)
│   │   ├── orchestrator_agent.py     # Master controller + iteration loop
│   │   ├── regional_agent.py         # GA+MILP regional solver
│   │   ├── coordinator_agent.py      # Conflict resolution + feedback
│   │   └── service_generator_agent.py # Candidate service pool builder
│   │
│   ├── optimization/                 # Solver implementations
│   │   ├── data.py                   # Port, Service, Demand, Problem dataclasses
│   │   ├── hierarchical_ga.py        # Two-level GA orchestrator
│   │   ├── service_ga.py             # Service selection GA (DEAP-style)
│   │   ├── frequency_ga.py           # Frequency assignment GA
│   │   ├── hub_milp.py               # PuLP-based flow MILP
│   │   └── flow_optimizer.py         # Post-solve metrics extractor
│   │
│   ├── decomposition/                # Problem decomposition
│   │   ├── port_clustering.py        # K-means geographic clustering
│   │   └── regional_splitter.py      # Zero-duplication demand splitter
│   │
│   ├── data/                         # Data loading and preprocessing
│   │   ├── network_loader.py         # CSV → Problem instance loader
│   │   ├── preprocess.py             # Data cleaning and validation
│   │   └── graph_builder.py          # Adjacency and distance utilities
│   │
│   ├── services/                     # Service generation logic
│   │   ├── hub_detector.py           # Hub scoring (demand + connectivity)
│   │   └── candidate_service_generator.py  # Heuristic service builder
│   │
│   ├── llm/                          # LLM integration
│   │   ├── client.py                 # OpenRouter client (caching, fallback)
│   │   ├── evaluator.py              # Response quality scoring
│   │   ├── evaluator_manager.py      # Singleton evaluator
│   │   └── metrics.py                # LLM call telemetry
│   │
│   └── utils/                        # Cross-cutting utilities
│       ├── config.py                 # Environment-based configuration
│       └── logger.py                 # Structured logging (structlog)
│
├── tests/                            # Test suite
│   ├── test_orchestrator.py          # End-to-end pipeline test (9 sections)
│   ├── test_regional_agent.py        # Regional GA+MILP integration test
│   ├── test_ga.py                    # ServiceGA / FrequencyGA / HierarchicalGA
│   ├── test_milp.py                  # HubMILP solver test
│   ├── test_clustering.py            # PortClustering test
│   ├── test_data_loader.py           # NetworkLoader test
│   ├── test_service_generation.py    # CandidateServiceGenerator test
│   └── test_llm.py                   # LLM client + cache test
│
├── docs/                             # Documentation
│   ├── SYSTEM_ARCHITECTURE.md        # Architecture deep-dive
│   ├── DEVELOPER_GUIDE.md            # Developer onboarding
│   ├── DATA_DICTIONARY.md            # Data structures and schemas
│   ├── RUNBOOK.md                    # Operational procedures
│   └── FAQ.md                        # Common questions
│
├── data/                             # Datasets (not tracked in git)
│   └── raw/                          # WorldLarge benchmark CSVs
│       ├── ports.csv                 # 435 ports (UNLocode, coordinates, costs)
│       ├── Demand_WorldLarge.csv     # 9,600 OD demand corridors (TEU, revenue)
│       ├── fleet_WorldLarge.csv      # Vessel fleet parameters
│       └── dist_dense.csv            # Port-to-port distances (nautical miles)
│
├── deployment/                       # Deployment manifests
│   ├── docker-compose.yml            # Multi-service local deployment
│   └── k8s/                          # Kubernetes manifests
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
│
├── ARCHITECTURE_AUDIT_REPORT.md      # Engineering audit with issue prioritization
├── SYSTEM_ARCHITECTURE_ANALYSIS.md  # Complete execution flow and bottleneck analysis
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

---

## Dataset

The system uses the **WorldLarge** benchmark from the liner shipping research community:

| File | Contents | Size |
|------|----------|------|
| `ports.csv` | 435 ports with UNLocode, lat/lon, handling cost, draft | 435 rows |
| `Demand_WorldLarge.csv` | OD demand corridors (FFE/week, revenue per TEU) | 9,600 rows |
| `dist_dense.csv` | Great-circle distances between port pairs (NM) | ~189K entries |
| `fleet_WorldLarge.csv` | Vessel types, capacities, operating costs | ~50 vessel classes |

**Note:** Data files are not tracked in this repository due to size. Place them in `data/raw/` before running.

---

## Quick Start

### Prerequisites

- Python 3.10+
- 8 GB RAM minimum (16 GB recommended for WorldLarge)
- OpenRouter API key (for LLM-assisted decisions)

### Installation

```bash
git clone https://github.com/112301021/Liner_shipping_optimizer.git
cd Liner_shipping_optimizer/shipping_optimizer

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set OPENROUTER_API_KEY
```

### Run Optimization (Programmatic)

```python
from src.agents.orchestrator_agent import OrchestratorAgent
from src.data.network_loader import NetworkLoader

loader = NetworkLoader()
network = loader.load_network()

from src.optimization.data import Problem
problem = Problem(
    ports=network["ports"],
    services=[],
    demands=network["demands"],
    distance_matrix=network["distance_matrix"]
)

orchestrator = OrchestratorAgent()
result = orchestrator.process({"problem": problem})

metrics = result["summary_metrics"]
print(f"Annual Profit : ${metrics['annual_profit']:,.0f}")
print(f"Coverage      : {metrics['coverage']:.1f}%")
print(f"Services      : {metrics['total_services']}")
print(f"Iterations    : {result['iterations_run']}")
```

### Run with WebSocket Backend

```bash
python backend/main.py
# Open frontend at http://localhost:5173
```

### Run Tests

```bash
pytest tests/test_clustering.py tests/test_ga.py tests/test_milp.py -v

# Full pipeline integration test (5–10 minutes)
python tests/test_orchestrator.py
```

---

## Docker Deployment

```bash
# Build
docker build -t liner-shipping-optimizer .

# Run with API key
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=sk-or-... \
  -v $(pwd)/data:/app/data \
  liner-shipping-optimizer

# Multi-service via Compose
docker-compose up --build
```

---

## Configuration

All parameters are environment-variable driven:

```bash
# .env
OPENROUTER_API_KEY=sk-or-...
ORCHESTRATOR_MODEL=openrouter/gpt-oss-120b
REGIONAL_MODEL=meta-llama/llama-3.1-8b-instruct

# GA Parameters
GA_POPULATION_SIZE=80       # adaptive override: 60–140
GA_GENERATIONS=120          # adaptive override: 60–180
MILP_TIME_LIMIT=120         # seconds per hub MILP subproblem

# Optimization Constants
MAX_TRANSFER_PAIRS=2000     # MILP transfer variable cap
COVERAGE_TARGET=70          # % minimum coverage target
MAX_ITERATIONS=3            # feedback loop hard cap
```

---

## API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/optimize` | Start an optimization run |
| `GET` | `/api/results/{run_id}` | Retrieve optimization results |
| `GET` | `/api/health` | System health check |

### WebSocket Events

```
ws://localhost:8000/ws/stream
```

| Event | Payload |
|-------|---------|
| `pipeline_started` | `{problem_size: {ports, lanes, services}}` |
| `stage_started` | `{stage, stage_id}` |
| `stage_completed` | `{stage, stage_id, ...metrics}` |
| `region_updated` | `{data: {region_id, profit, coverage, services, ...}}` |
| `iteration_completed` | `{iteration, profit, coverage, convergence_score}` |
| `convergence_reached` | `{iteration, score, reason}` |
| `pipeline_completed` | `{data: {results: {...}}}` |

---

## Performance Characteristics

| Instance | Ports | Demands | Services | Runtime | Memory |
|----------|-------|---------|----------|---------|--------|
| Small | 50 | 500 | 200 | < 1 min | ~10 MB |
| Medium | 200 | 2,000 | 800 | 3–5 min | ~50 MB |
| WorldLarge | 435 | 9,600 | ~1,200 | 5–10 min | ~200 MB |

**Optimization convergence** (typical WorldLarge run):

| Iteration | Coverage | Profit/week | Conv. Score |
|-----------|----------|-------------|-------------|
| 0 (initial) | ~55% | ~$8M | 0.52 |
| 1 (post-feedback) | ~65% | ~$12M | 0.71 |
| 2 (post-feedback) | ~72% | ~$14M | 0.88 |

---

## Architecture Audit Summary

A detailed engineering audit (`ARCHITECTURE_AUDIT_REPORT.md`) identifies the following:

**Critical issues (production blockers):**
- Mutable `Problem` object shared across iterations — requires immutable snapshots
- O(n²) distance lookups in `HubMILP` — requires `@lru_cache` memoization
- Synchronous regional execution via `ThreadPoolExecutor` — requires `asyncio.gather`

**High priority:**
- WebSocket event schema inconsistency between backend components
- In-memory state management (no horizontal scaling)
- Hardcoded `MAX_TRANSFER_PAIRS=2000` risks infeasibility on dense networks

**Production readiness path:**
1. Distance memoization (quick win, 2–5× MILP speedup)
2. Immutable problem snapshots (correctness)
3. Full async refactor (scalability)
4. Redis-based distributed state (horizontal scaling)
5. PostgreSQL migration (production persistence)

---

## Research Directions

This system provides a foundation for several open research problems:

- **Adaptive decomposition**: dynamic region count based on demand density, not just port count
- **Warm-start MILP**: use previous-iteration flows as initial bounds for faster convergence
- **Carbon-aware optimization**: add emission cost terms to the objective function
- **Stochastic demand**: robust optimization under demand uncertainty using scenario-based MILP
- **Reinforcement learning for weight tuning**: replace the LLM feedback loop with a learned policy
- **Distributed MILP**: solve hub cluster subproblems in parallel across workers

---

## Contributing

See [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for architecture conventions, testing requirements, and contribution workflow.

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/async-orchestration`)
3. Add tests for new functionality
4. Ensure `pytest tests/` passes
5. Submit a pull request with a clear description of changes

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Citation

If you use this system in research, please cite:

```
@software{liner_shipping_optimizer_2025,
  author    = {Mallameeda, Ajay Kumar},
  title     = {Liner Shipping Network Optimizer: A Distributed GA+MILP Platform},
  year      = {2025},
  institution = {IIT Palakkad},
  url       = {https://github.com/112301021/Liner_shipping_optimizer}
}
```
