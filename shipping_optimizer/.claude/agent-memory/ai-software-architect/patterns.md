# Patterns & Anti-Patterns
# Confirmed observations across multiple sessions.
# Only write here after verifying in actual code — not speculation.

---

## CONFIRMED ANTI-PATTERNS

### Pattern: Mutable Problem Object
File: src/agents/orchestrator_agent.py, Line: 268
Description: Problem object mutated in-place during feedback loop
Root Cause: Direct attribute assignment without copying
Impact: State corruption risk, difficult to debug iterations
Fix Applied: No - needs immutable snapshot pattern
Date Confirmed: 2026-05-15

### Pattern: Repeated Distance Matrix Lookups
File: src/optimization/hub_milp.py, Line: 99
Description: O(n²) distance access without caching
Root Cause: Direct dictionary access in tight loops
Impact: Performance bottleneck in MILP solve
Fix Applied: No - needs memoization
Date Confirmed: 2026-05-15

### Pattern: Synchronous Regional Execution
File: src/agents/orchestrator_agent.py, Line: 391
Description: ThreadPoolExecutor but then wait for all futures
Root Cause: Using executor but collecting results synchronously
Impact: No true parallelism, serialization bottleneck
Fix Applied: No - needs async/await refactor
Date Confirmed: 2026-05-15

---

## GOOD PATTERNS (preserve these)

### Pattern: Zero-Duplication Demand Splitting
File: src/decomposition/regional_splitter.py
Description: Origin-based assignment ensures no demand duplication
Why It Works: Validates demand conservation mathematically
Date Confirmed: 2026-05-15

### Pattern: Hierarchical GA → MILP Pipeline
File: src/agents/regional_agent.py, Line: 184
Description: Service selection then routing optimization
Why It Works: Reduces MILP complexity by pre-selecting services
Date Confirmed: 2026-05-15

### Pattern: Smart Service Filtering
File: src/agents/regional_agent.py, Line: 61
Description: Margin and coverage-based pruning before optimization
Why It Works: Reduces search space while maintaining solution quality
Date Confirmed: 2026-05-15

---

## CODE SMELL REGISTRY

| Smell | Location | Severity | Status |
|---|---|---|---|
| In-place problem mutation | agents/orchestrator_agent.py | High | Open |
| Missing distance cache | optimization/hub_milp.py | Medium | Open |
| LLM calls in hot path | agents/*.py | Medium | Open |
| Hardcoded constants | optimization/*.py | Low | Open |
| No input validation | data/network_loader.py | Medium | Open |

---

## NAMING CONVENTIONS OBSERVED

- [x] Confirmed: `region` used consistently (no `area` found)
- [x] Confirmed: GA methods use `run()`, MILP methods use `solve()`
- [x] Confirmed: Agent names follow `*_agent.py` pattern
- [x] Confirmed: Problem attributes use snake_case

---

## STRUCTURAL PATTERNS

### Module Coupling Map
```
agents/ ──depends──> optimization/
agents/ ──depends──> decomposition/
agents/ ──depends──> services/
optimization/ ──depends──> data/
backend/ ──depends──> agents/ (via sys.path)
```

### Classes Confirmed Over 200 Lines
| Class | File | Lines (approx) | Refactor Priority |
|-------|------|----------------|-------------------|
| OrchestratorAgent | agents/orchestrator_agent.py | 684 | High |
| RegionalAgent | agents/regional_agent.py | 341 | Medium |
| HubMILP | optimization/hub_milp.py | 300+ | Medium |

---

## SAFE REFACTORING WINS APPLIED

<!-- Record completed refactors so we never redo or undo them accidentally -->
| Refactor | File | Date | Result |
|----------|------|------|--------|
| | | | |