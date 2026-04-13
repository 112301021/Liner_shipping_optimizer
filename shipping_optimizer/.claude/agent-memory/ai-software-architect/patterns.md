# Patterns & Anti-Patterns
# Confirmed observations across multiple sessions.
# Only write here after verifying in actual code — not speculation.

---

## CONFIRMED ANTI-PATTERNS

### [TEMPLATE — copy this block when adding a new pattern]
```
Pattern: [name]
File: [path/to/file.py], Line: [N]
Description: [what the code does wrong]
Root Cause: [why it was written this way]
Impact: [correctness / performance / maintainability]
Fix Applied: [yes/no — brief description if yes]
Date Confirmed: [YYYY-MM-DD]
```

---

## GOOD PATTERNS (preserve these)

### [TEMPLATE — copy this block when adding a good pattern]
```
Pattern: [name]
File: [path/to/file.py]
Description: [what the code does well]
Why It Works: [brief explanation]
Date Confirmed: [YYYY-MM-DD]
```

---

## CODE SMELL REGISTRY

| Smell                  | Location          | Severity | Status     |
|------------------------|-------------------|----------|------------|
| [Add as discovered]    |                   |          |            |

---

## NAMING CONVENTIONS OBSERVED

- [ ] Verify: `region` vs `area` inconsistency in `agents/`
- [ ] Verify: solver method naming consistency across GA and MILP
- [ ] Add confirmed conventions here as discovered

---

## STRUCTURAL PATTERNS

### Module Coupling Map
```
[Update this as you trace dependencies]

agents/ ──depends──> optimization/
optimization/ ──depends──> data/
api/ ──depends──> agents/
```

### Classes Confirmed Over 200 Lines
| Class | File | Lines (approx) | Refactor Priority |
|-------|------|----------------|-------------------|
| [Add as found] | | | |

---

## SAFE REFACTORING WINS APPLIED

<!-- Record completed refactors so we never redo or undo them accidentally -->
| Refactor | File | Date | Result |
|----------|------|------|--------|
| [Add as applied] | | | |

