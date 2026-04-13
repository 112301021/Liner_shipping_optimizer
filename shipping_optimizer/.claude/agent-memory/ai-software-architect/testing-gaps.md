# Testing Gaps Registry
# Missing tests identified across the project.
# Update after every code review or test analysis session.

---

## TESTING PHILOSOPHY FOR THIS PROJECT

Priority order for test coverage:
1. **Correctness tests** — does solve() return valid assignments?
2. **Edge cases** — zero vessels, zero demand, max capacity overflow
3. **Failure boundaries** — invalid inputs, missing files, solver divergence
4. **Integration tests** — full pipeline from RegionalAgent to ProfitEvaluator
5. **Performance tests** — does it finish within time limits on large data?

---

## CRITICAL MISSING TESTS (suspected — verify against tests/ directory)

### DeploymentOptimizer
- [ ] `solve()` with zero vessels available
- [ ] `solve()` with zero cargo demand
- [ ] `solve()` when solver returns None (infeasible)
- [ ] `solve()` with negative demand values
- [ ] `solve()` with capacity exactly at limit (boundary)
- [ ] `solve()` with capacity exceeded by 1 unit (overflow boundary)

### ServiceGeneratorAgent
- [ ] `create()` with empty route list
- [ ] `create()` with duplicate route IDs
- [ ] `create()` under concurrent access (thread safety)
- [ ] `create()` when optimization layer returns None

### RegionalAgent
- [ ] Correct splitting of problem by region boundaries
- [ ] Handling of region with zero ports
- [ ] Handling of region with single port

### DataLoader
- [ ] Missing input file → graceful error (not crash)
- [ ] Malformed JSON/CSV → graceful error with message
- [ ] Empty data file → clear error returned
- [ ] Partial data (some fields missing) → validation failure reported

### GA Solver
- [ ] Convergence within max generations
- [ ] Behavior when all individuals are infeasible
- [ ] Population size = 1 (edge case)
- [ ] Mutation rate = 0 (no exploration)
- [ ] Fitness function returning NaN or inf

### MILP Solver
- [ ] Infeasible problem → returns None, not exception
- [ ] Unbounded problem → handled gracefully
- [ ] Timeout → returns best found so far, not crash

### ProfitEvaluator
- [ ] Zero profit assignment (all routes unprofitable)
- [ ] Negative profit (cost exceeds revenue)
- [ ] Assignment with no cargo assigned to any vessel

---

## TEST COVERAGE MAP

Update this table as you inspect `tests/` directory:

| Module | Test File | Coverage Est. | Critical Gaps |
|--------|-----------|---------------|---------------|
| DeploymentOptimizer | [verify] | [verify] | solve() edge cases |
| ServiceGeneratorAgent | [verify] | [verify] | concurrent access |
| RegionalAgent | [verify] | [verify] | zero-port region |
| DataLoader | [verify] | [verify] | missing file handling |
| GA Solver | [verify] | [verify] | convergence failure |
| MILP Solver | [verify] | [verify] | infeasible handling |
| ProfitEvaluator | [verify] | [verify] | negative profit |

---

## TEST TEMPLATES

### Edge Case Test Template
```python
def test_solve_with_zero_vessels():
    """DeploymentOptimizer must handle zero vessels gracefully."""
    optimizer = DeploymentOptimizer(vessels=[], cargo=sample_cargo())
    result = optimizer.solve()
    assert result is not None
    assert result.feasible == False
    assert result.assignments == []

def test_solve_returns_none_on_infeasible():
    """Solver must return None (not raise) when problem is infeasible."""
    optimizer = DeploymentOptimizer(vessels=tiny_fleet(), cargo=massive_cargo())
    result = optimizer.solve()
    # Should not raise — should return gracefully
    assert result is None or result.feasible == False
```

### Integration Test Template
```python
def test_full_pipeline_small_case():
    """End-to-end: RegionalAgent → ServiceGenerator → Optimizer → Evaluator."""
    region_config = load_test_fixture("small_region.json")
    agent = RegionalAgent(region_config)
    deployment = agent.run()
    assert deployment is not None
    assert deployment.total_profit >= 0
    assert all(a.vessel_id is not None for a in deployment.assignments)
```

---

## TESTS ADDED (track progress)

| Test | File | Date Added | Result |
|------|------|------------|--------|
| [Add as tests are written] | | | |

