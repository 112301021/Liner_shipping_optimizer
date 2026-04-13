# Performance Engineering Log
# Bottlenecks found, caching applied, complexity improvements, memory wins.
# Update after every performance analysis or optimization session.

---

## PERFORMANCE PRIORITY ORDER

1. Fix correctness first — a fast wrong answer is worthless
2. Eliminate O(n²) and worse — biggest gains
3. Add caching for repeated calculations
4. Reduce memory allocations in hot paths
5. Use generators instead of lists where possible
6. Profile before micro-optimizing

---

## COMPLEXITY HOTSPOT REGISTRY

### [TEMPLATE]
```
ID: PERF-###
Location: [file.py], function [name()], Line [N]
Current Complexity: O(?)
Target Complexity: O(?)
Description: [what the loop/function does]
Fix Applied: [yes/no — describe if yes]
Estimated Speedup: [rough estimate]
Status: [OPEN / FIXED]
Date: [YYYY-MM-DD]
```

---

## SUSPECTED BOTTLENECKS (verify in code)

### PERF-001: Distance Calculation — likely O(n²)
- **Location**: Suspected in `optimization/` solver internals
- **Issue**: Route distance likely recalculated on every solver iteration
- **Fix Pattern**:
  ```python
  # Before: recomputed every call
  def get_distance(port_a, port_b):
      return haversine(port_a.coords, port_b.coords)

  # After: precompute once
  class DistanceMatrix:
      def __init__(self, ports):
          self._matrix = {
              (a.id, b.id): haversine(a.coords, b.coords)
              for a in ports for b in ports
          }
      def get(self, port_a_id, port_b_id):
          return self._matrix[(port_a_id, port_b_id)]
  ```
- **Expected Speedup**: 10x–100x on large route sets
- **Status**: SUSPECTED — confirm with profiling

### PERF-002: Profit Evaluation Inside GA Loop
- **Location**: Suspected in GA solver, evaluation step
- **Issue**: ProfitEvaluator may be called for every individual in every generation without memoization
- **Fix Pattern**:
  ```python
  from functools import lru_cache

  @lru_cache(maxsize=10000)
  def evaluate_profit(route_tuple):
      return profit_evaluator.compute(route_tuple)
  ```
- **Status**: SUSPECTED — confirm with profiling

### PERF-003: Late Constraint Filtering
- **Location**: Suspected in DeploymentOptimizer output stage
- **Issue**: Invalid assignments may be generated and only filtered at output, wasting solver cycles
- **Fix**: Apply feasibility constraints at the candidate generation stage, not post-processing
- **Status**: SUSPECTED — confirm in code

---

## CONFIRMED PERFORMANCE WINS

<!-- Move from suspected to here once fix is applied and verified -->
| ID | Fix | Before | After | Date |
|----|-----|--------|-------|------|
| [Add as fixed] | | | | |

---

## MEMORY OPTIMIZATION LOG

### Object Creation in Loops
```
Watch for: creating new dicts/lists inside tight loops
Fix: pre-allocate or reuse structures
```

### Generator Opportunities
```python
# Anti-pattern: building full list in memory
all_routes = [build_route(r) for r in raw_routes]

# Better: use generator if consuming one at a time
all_routes = (build_route(r) for r in raw_routes)
```

### Confirmed Memory Issues
| Issue | File | Fixed? | Date |
|-------|------|--------|------|
| [Add as found] | | | |

---

## PROFILING GUIDE

When the user reports slowness, follow this order:

1. Ask: which function / which step is slow?
2. Check PERF registry above for known issues first
3. Look for nested loops in the reported module
4. Check if distance/profit calculations are cached
5. Check if constraint filtering happens early or late
6. Suggest adding timing logs:
   ```python
   import time
   start = time.perf_counter()
   result = slow_function()
   elapsed = time.perf_counter() - start
   logger.info(f"slow_function took {elapsed:.3f}s")
   ```

---

## CACHING STRATEGY REFERENCE

| Calculation Type | Recommended Cache | Notes |
|-----------------|-------------------|-------|
| Port-to-port distance | Pre-computed matrix (dict of dicts) | Compute once at startup |
| Route profit score | `lru_cache` or dict keyed by route tuple | Clear if vessel constraints change |
| Feasibility check | Dict keyed by (route, vessel) pair | Clear if capacity changes |
| Regional demand | Load once, pass by reference | Never re-read from disk in loop |

