# Debugging Log
# Recurring bugs, root causes, fixes applied, and lessons learned.
# Update after every debugging session. Most recent at top.

---

## HOW TO USE THIS FILE

When you debug an error:
1. Check this file FIRST — the same bug may have appeared before
2. If new, add it at the top of the Bug Registry
3. If resolved, mark status as FIXED and record the fix

---

## BUG REGISTRY

### [TEMPLATE — copy this block for each new bug]
```
ID: BUG-###
Title: [short description]
File: [path/to/file.py], Line: [N]
Error Type: [KeyError / AttributeError / RuntimeError / etc.]
Symptom: [what the user observed]
Root Cause: [WHY it happened — design flaw, bad assumption, missing check]
Fix Applied: [code change made]
Recurrence Risk: [low / medium / high]
Status: [OPEN / FIXED / DEFERRED]
Date: [YYYY-MM-DD]
```

---

## KNOWN FAILURE MODES (suspected — verify in code)

These are failure modes identified from agent design analysis.
Move to Bug Registry once confirmed in actual runtime.

### 1. Missing File Crash in data_loader
- **Risk**: If input data file is missing, loader likely raises unhandled exception
- **Module**: `data/` — data loader
- **Fix Pattern**:
  ```python
  try:
      with open(filepath, 'r') as f:
          data = json.load(f)
  except FileNotFoundError:
      logger.error(f"Data file not found: {filepath}")
      return None  # or raise custom exception
  except json.JSONDecodeError as e:
      logger.error(f"Malformed data file {filepath}: {e}")
      return None
  ```
- **Status**: SUSPECTED — verify next time data/ is analyzed

### 2. KeyError in Service Generator
- **Risk**: KeyError when accessing route/vessel keys that may not exist in dict
- **Module**: `agents/service_generator_agent.py`
- **Fix Pattern**: Use `.get(key, default)` instead of `dict[key]`
- **Status**: SUSPECTED — verify on next error report

### 3. Convergence Failure in MILP Solver
- **Risk**: Solver may return infeasible/None without caller checking
- **Module**: `optimization/` — MILP solver
- **Fix Pattern**:
  ```python
  result = milp_solver.solve()
  if result is None or result.status != 'optimal':
      logger.warning(f"Solver did not converge: {result.status if result else 'None'}")
      return fallback_solution()
  ```
- **Status**: SUSPECTED — verify on next optimization error

---

## DEBUGGING DECISION RULES

These rules speed up root cause analysis — apply in order:

1. **KeyError** → check dict key assumptions, use `.get()` with defaults
2. **AttributeError** → check None returns from upstream modules
3. **IndexError** → check empty list handling before indexing
4. **RecursionError** → check for missing base case or circular call
5. **Timeout / slow** → check for O(n²) loops, missing caching
6. **Wrong results** → check constraint passing between modules (cross-module bug)
7. **Convergence failure** → check solver input validity before calling solve()

---

## EXECUTION CHAIN TRACE GUIDE

When debugging, trace through this chain and note WHERE data changes:

```
Step 1: Orchestrator — validates inputs, dispatches to regions
Step 2: RegionalAgent — splits problem by region, calls ServiceGeneratorAgent
Step 3: ServiceGeneratorAgent — builds service routes, calls DeploymentOptimizer
Step 4: DeploymentOptimizer — runs GA or MILP solver
Step 5: GA/MILP Solver — returns solution or None
Step 6: ProfitEvaluator — evaluates solution, returns score
Step 7: Coordinator — aggregates regional results
```

Mark the step where the failure first occurs — that is the localization point.

---

## LESSONS LEARNED

<!-- Add after resolving non-obvious bugs -->
| Lesson | Context | Date |
|--------|---------|------|
| [Add as discovered] | | |

