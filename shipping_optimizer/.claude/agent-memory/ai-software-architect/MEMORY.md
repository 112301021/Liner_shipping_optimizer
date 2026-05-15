# AI Software Architect — Persistent Memory
# Loaded into system prompt every session. KEEP UNDER 200 LINES.
# Last updated: [agent updates this after each session]

---

## PROJECT IDENTITY

- **Project**: Liner Shipping Optimizer
- **Root**: `C:\Users\M AJAY KUMAR\Liner_shipping_optimizer\shipping_optimizer\`
- **Language**: Python
- **Domain**: Maritime logistics — vessel routing, cargo deployment, profit optimization

---

## CRITICAL EXECUTION PIPELINE

```
Orchestrator
  └── RegionalAgent
        └── ServiceGeneratorAgent
              └── DeploymentOptimizer
                    ├── GA Solver
                    ├── MILP Solver
                    └── ProfitEvaluator
```

Always trace issues through this full chain. Never analyze a single file in isolation.

---

## KEY DIRECTORY MAP

| Directory       | Purpose                                      |
|-----------------|----------------------------------------------|
| `agents/`       | Regional agents, service generator agents    |
| `optimization/` | Solvers (GA, MILP), deployment optimizer     |
| `data/`         | Data loaders, preprocessing pipelines        |
| `tests/`        | Unit and integration tests                   |
| `api/`          | External endpoints and interfaces            |
| `.claude/agent-memory/ai-software-architect/` | This memory directory |

---

## KNOWN ARCHITECTURAL RISKS (update as confirmed)

- [x] `DeploymentOptimizer` suspected to exceed 800 lines — NOT FOUND (actual: HubMILP 300+ lines)
- [x] `data_loader` may lack try/except on file read — CONFIRMED (missing file handling)
- [x] Distance calculations may be recomputed without caching — CONFIRMED (O(n²) in hub_milp.py)
- [x] Naming inconsistency suspected: `region` vs `area` across agents — RESOLVED (consistent naming)

> Confirmed issues moved to `patterns.md`.

---

## ANALYSIS DEFAULTS

- Health score baseline: start at 10.0, deduct per issue severity
  - CRITICAL: −1.5 each
  - HIGH: −0.7 each
  - MEDIUM: −0.3 each
  - LOW: −0.1 each
- Confidence level: state explicitly in every report
- Always provide both Minimal Fix and Optimal Fix

---

## USER PREFERENCES

- Output format: structured report (see agent prompt for template)
- Communication style: precise, no fluff, engineering-grade
- Fix preference: minimal change first, then optimal
- Memory: update after every session with confirmed patterns

---

## TOPIC FILES (detailed notes — link from here)

| File               | Contents                                      |
|--------------------|-----------------------------------------------|
| `patterns.md`      | Confirmed code patterns and anti-patterns     |
| `debugging.md`     | Recurring bugs, root causes, fixes applied    |
| `architecture.md`  | Module structure, decisions, layer map        |
| `performance.md`   | Bottlenecks, caching wins, complexity fixes   |
| `testing-gaps.md`  | Missing tests identified across the project   |

---

## SESSION LOG (most recent first — agent appends here)

<!-- Agent: append a one-line summary after each session -->
<!-- Format: [YYYY-MM-DD] Brief description of what was analyzed and key finding -->
[2026-05-15] Complete architectural audit: Created SYSTEM_ARCHITECTURE_ANALYSIS.md with full pipeline, bottlenecks, and production risks
[2026-05-15] Confirmed critical bottlenecks: O(n²) distance lookups, mutable problem state, synchronous regional execution
[2026-05-15] Identified production scalability issues: Single-threaded execution, no horizontal scaling, WebSocket not production-ready
[2026-05-09] Complete end-to-end architectural audit: Found functional AI pipeline but broken real-time dashboard integration due to WebSocket mismatches and mock data usage
[2026-05-09] Identified critical frontend disconnect: maritime_dashboard.jsx uses hardcoded DATA, no WebSocket client implemented
[2026-05-09] Discovered event schema inconsistency: main.py validates events via EventValidator but real_orchestrator_integration.py sends raw dicts

