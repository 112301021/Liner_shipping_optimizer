# Architecture Reference
# Module structure, layer decisions, dependency map, and interface contracts.
# Update whenever architectural decisions are made or discovered.

---

## SYSTEM OVERVIEW

**Domain**: Liner Shipping Optimization
**Problem**: Assign vessels to cargo routes across regions to maximize profit
**Approach**: Hierarchical optimization — regional decomposition → service generation → deployment optimization

---

## LAYER MAP

```
┌─────────────────────────────────────────┐
│               API Layer                 │  ← External interface (api/)
│    endpoints, request validation         │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│            Agent Layer                  │  ← agents/
│  Orchestrator, RegionalAgent,           │
│  ServiceGeneratorAgent                  │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│         Optimization Layer              │  ← optimization/
│  DeploymentOptimizer, GA, MILP,         │
│  ProfitEvaluator                        │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│            Data Layer                   │  ← data/
│  DataLoader, Preprocessing              │
└─────────────────────────────────────────┘
```

**Rule**: Each layer should ONLY call the layer directly below it.
**Violation to watch for**: API layer calling optimization/ directly — introduce adapter if found.

---

## MODULE RESPONSIBILITY MAP

| Module | File(s) | Single Responsibility | Confirmed? |
|--------|---------|-----------------------|------------|
| Orchestrator | `agents/orchestrator.py` (suspected) | Dispatch to regional agents | [ ] |
| RegionalAgent | `agents/regional_agent.py` (suspected) | Split problem by region | [ ] |
| ServiceGeneratorAgent | `agents/service_generator_agent.py` | Build service route configs | [ ] |
| DeploymentOptimizer | `optimization/deployment_optimizer.py` | Run solver, return deployment | [ ] |
| GA Solver | `optimization/ga_solver.py` (suspected) | Genetic algorithm optimization | [ ] |
| MILP Solver | `optimization/milp_solver.py` (suspected) | Integer programming solver | [ ] |
| ProfitEvaluator | `optimization/profit_evaluator.py` (suspected) | Score a given deployment | [ ] |
| DataLoader | `data/data_loader.py` (suspected) | Load and validate input data | [ ] |

> Mark [ ] as [x] and add actual file paths as you confirm them.

---

## INTERFACE CONTRACTS

These are the expected input/output contracts between modules.
Update as you discover actual signatures.

### RegionalAgent → ServiceGeneratorAgent
```python
# Expected input
region_config: dict  # {region_id, vessels, cargo_demand, constraints}

# Expected output
service_routes: list  # [{route_id, stops, vessel_id, cargo_assigned}]
```

### ServiceGeneratorAgent → DeploymentOptimizer
```python
# Expected input
service_config: dict  # {routes, vessels, constraints, objective}

# Expected output
deployment: dict  # {assignments, total_profit, feasible: bool}
```

### DeploymentOptimizer → GA/MILP Solver
```python
# Expected input
problem: OptimizationProblem  # (verify actual class name)

# Expected output
solution: Solution | None  # None if infeasible
```

> Update with actual type signatures as discovered.

---

## ARCHITECTURAL DECISIONS MADE

<!-- Record decisions so we don't accidentally reverse them -->
| Decision | Rationale | Date | Made By |
|----------|-----------|------|---------|
| [Add as discovered or decided] | | | |

---

## KNOWN COUPLING RISKS

| Coupling | From | To | Risk Level | Fix |
|----------|------|----|------------|-----|
| Suspected direct solver access | ServiceGeneratorAgent | DeploymentOptimizer internals | HIGH | AbstractSolver interface |
| [Add as confirmed] | | | | |

---

## REFACTORING CANDIDATES

| Class/Module | Issue | Suggested Split | Priority |
|-------------|-------|-----------------|----------|
| DeploymentOptimizer (suspected 800+ lines) | SRP violation | VesselAssignment, CargoRouting, ProfitEvaluation | HIGH |
| [Add as confirmed] | | | |

---

## CIRCULAR DEPENDENCY WATCH

Modules that are at risk of circular imports — verify:
- [ ] `agents/` importing from `optimization/` while `optimization/` imports from `agents/`
- [ ] `data/` importing from `agents/` (should never happen — data is lowest layer)

