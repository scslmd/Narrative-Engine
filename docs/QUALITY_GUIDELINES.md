# Universal Quality Guidelines

> A reusable framework for evaluating and ensuring high-quality work. Evocable at any time.

---

## Core Philosophy

**Quality is multi-dimensional and measurable.** A high-quality change must satisfy multiple criteria simultaneously, not just "work."

---

## Universal Quality Dimensions

### 1. Contract Adherence

**Principle:** Use exact interfaces, endpoints, and field names defined by the system.

**Checklist:**
- [ ] Use exact interfaces/endpoints defined by the system
- [ ] Do not invent workarounds for uncertain contracts
- [ ] Preserve naming conventions at appropriate boundaries
- [ ] Do not rename fields just for convenience

**Scoring:**
- `0`: Wrong interface, wrong payload, wrong assumptions
- `1`: Mostly correct, but manually adapts around uncertain details
- `2`: Uses exact contract already defined by the system

---

### 2. Architectural Consistency

**Principle:** Follow established patterns rather than inventing new ones.

**Checklist:**
- [ ] Use shared utilities and clients instead of duplicating configuration
- [ ] Maintain consistency in error handling, state management, and data flow
- [ ] Do not reinvent patterns that already exist
- [ ] Extend existing abstractions rather than creating parallel ones

**Scoring:**
- `0`: Every file invents its own pattern
- `1`: Some consistency, but mixed conventions
- `2`: One clear pattern for the relevant concern

---

### 3. State Correctness

**Principle:** State synchronization must survive edge cases.

**Checklist:**
- [ ] Source of truth is explicit and singular
- [ ] State survives edge cases (deep links, refreshes, restarts)
- [ ] Avoid fragile parsing or brittle assumptions
- [ ] Route/state remain synchronized across navigation methods

**Scoring:**
- `0`: Depends on fragile logic or stale state
- `1`: Works for common paths but brittle for edge cases
- `2`: Survives reloads, direct navigation, and edge cases

---

### 4. Production Readiness

**Principle:** Remove all prototype artifacts before merging.

**Checklist:**
- [ ] No console logs in user-facing code paths
- [ ] No dead buttons or non-functional CTAs
- [ ] No placeholder data or "for now" assumptions
- [ ] Every user-facing action has a real implementation

**Scoring:**
- `0`: Contains obvious prototype artifacts
- `1`: Mostly removed, but one or two remain
- `2`: No user-facing prototype seams remain

---

### 5. Error Resilience

**Principle:** Handle edge cases explicitly and appropriately.

**Checklist:**
- [ ] Loading states are explicit
- [ ] Empty states are explicit and suggest next steps
- [ ] Error states are recoverable where possible
- [ ] Meaningful error categories are distinguished (not all errors treated the same)
- [ ] Service layer handles technical details; presentation layer handles display

**Scoring:**
- `0`: Failures collapse into generic breakage
- `1`: Some errors handled, but not consistently
- `2`: Loading, error, and empty states are explicit and appropriate

---

### 6. User Experience Polish

**Principle:** Details matter; interactions should feel intentional.

**Checklist:**
- [ ] Labels and messages are readable and intentional
- [ ] Disabled states prevent invalid actions proactively
- [ ] No encoding artifacts or awkward interactions
- [ ] Buttons do what they claim
- [ ] State transitions feel deliberate

**Scoring:**
- `0`: Visible artifacts, broken labels, awkward flow
- `1`: Functionally usable, but rough around edges
- `2`: Labels, actions, and transitions feel production-ready

---

### 7. Type Safety

**Principle:** Types should express real contracts cleanly.

**Checklist:**
- [ ] Avoid excessive type casting
- [ ] Do not collapse rich shapes into lossy substitutes without reason
- [ ] Functions return established types whenever possible
- [ ] Component interfaces are explicit and narrow

**Scoring:**
- `0`: Works by fighting the type system
- `1`: Type-safe enough, but awkward or lossy in places
- `2`: Types express contracts cleanly with minimal casting

---

### 8. Static Analyzability

**Principle:** Use patterns that tools can analyze.

**Checklist:**
- [ ] Avoid dynamic patterns that defeat optimization or detection
- [ ] Use explicit conditional branches over dynamic string interpolation where tools matter
- [ ] Keep styling and configuration aligned with tool expectations

**Scoring:**
- `0`: Dynamic patterns tools cannot analyze
- `1`: Works, but some patterns are brittle
- `2`: Explicit patterns tools can reliably analyze

---

### 9. Boundary Discipline

**Principle:** Clear separation between modes and layers.

**Checklist:**
- [ ] Mock/test mode is explicit and contained
- [ ] Mock data matches real types
- [ ] Live mode does not keep mock-only artifacts
- [ ] Boundaries are explicit, not leaky

**Scoring:**
- `0`: Mock behavior leaks into live flows unpredictably
- `1`: Boundaries exist, but are noisy or inconsistent
- `2`: Mock mode is explicit, contained, and type-aligned

---

### 10. Maintainability

**Principle:** Changes should make future work easier.

**Checklist:**
- [ ] Changes reduce duplication, not increase it
- [ ] Intent is obvious without reverse-engineering
- [ ] Future extensions are easier after the change
- [ ] Logic is centralized when it appears in multiple places

**Scoring:**
- `0`: Works but makes code harder to extend
- `1`: Acceptable, but leaves new duplication or unclear intent
- `2`: Reduces duplication and makes future work easier

---

## Universal Quality Gate

**Do not consider work complete unless ALL of these are true:**

```
[ ] All automated checks pass (lint, typecheck, build, tests)
[ ] No warnings indicating real debt remain
[ ] No dead code or broken imports exist
[ ] All user-facing actions are functional
```

---

## Scoring Framework

### Scale

Use a **0-2 scale** per dimension:
- **0**: Broken or missing
- **1**: Partial or inconsistent
- **2**: Complete and consistent

### Target

**At least 80% of maximum score** (e.g., 17/20 for 10 dimensions)

### Calculation

```
Score = Sum of all dimension scores
Max   = Number of dimensions × 2
Target = Max × 0.8
```

---

## Automatic Failure Conditions

**Work is NOT high quality if ANY of these are true:**

- [ ] Automated checks fail
- [ ] Prototype artifacts remain in user-visible paths
- [ ] Dead or non-functional UI elements exist
- [ ] Configuration duplication exists where sharing is possible
- [ ] Placeholder assumptions remain in merged flows
- [ ] Visible artifacts (encoding, mojibake) remain
- [ ] Mock behavior leaks into live flows unnecessarily

---

## Layer-Specific Checklists

### Service/Utility Layer

**Applies to:** API clients, data access layers, utility modules

**Questions:**
- [ ] Uses shared configuration?
- [ ] Follows established patterns?
- [ ] Handles errors meaningfully?
- [ ] No duplicated logic?
- [ ] Returns established types?
- [ ] No mock-only logging left behind?

---

### Presentation/UI Layer

**Applies to:** Components, views, templates

**Questions:**
- [ ] All actions functional?
- [ ] Invalid states prevented proactively?
- [ ] Loading/empty/error states explicit?
- [ ] No debugging artifacts?
- [ ] No sample/demo behavior present?
- [ ] Labels readable and free of encoding issues?

---

### State/Architecture Layer

**Applies to:** Stores, routers, context providers, state machines

**Questions:**
- [ ] Source of truth explicit?
- [ ] Survives edge cases (refresh, deep link, restart)?
- [ ] Uses stable navigation/helpers?
- [ ] No unnecessary duplication?
- [ ] State transitions are deliberate?

---

## Final Self-Check Questions

**Before declaring work complete, answer these with "yes":**

1. [ ] Does every action have a real implementation?
2. [ ] Does every interface match the contract?
3. [ ] Did I remove all prototype artifacts?
4. [ ] Did I avoid duplicating existing utilities?
5. [ ] Can the flow survive edge cases?
6. [ ] Are all states (loading, empty, error) explicit?
7. [ ] Is the surface free of artifacts and brittle patterns?
8. [ ] Did all automated checks pass?

**If any answer is "no," the work is not complete.**

---

## Key Principles Summary

| Principle | Description |
|-----------|-------------|
| **Measure what matters** | Quality is multi-dimensional; score each dimension |
| **Automate the gate** | Use tools to enforce baseline quality |
| **Be explicit** | Source of truth, error states, and boundaries should be obvious |
| **Remove prototype debt** | Merged code should have no "for now" assumptions |
| **Consistency over cleverness** | Follow patterns rather than inventing solutions |
| **Prevent over recover** | Disable invalid actions rather than handling errors |
| **Future-proof** | Changes should make future work easier, not harder |

---

## How to Use This Document

### For Code Review

1. Select relevant dimensions for the change type
2. Score each dimension (0-2)
3. Calculate total score
4. Check automatic failure conditions
5. Run layer-specific checklist
6. Answer final self-check questions

### For Self-Assessment

1. Read through all dimensions
2. Score honestly
3. Identify gaps
4. Address gaps before marking complete

### For Team Standards

1. Adopt the 80% target as baseline
2. Customize dimensions for your domain
3. Add domain-specific automatic failure conditions
4. Integrate into CI/CD where possible

---

## Domain Adaptation Examples

### Backend/API Development

**Add these checks:**
- Database migrations are reversible
- API responses are versioned
- Error codes are meaningful
- Rate limiting is appropriate
- Authentication/authorization is verified

### DevOps/Infrastructure

**Add these checks:**
- Rollback procedure exists and is tested
- Monitoring/alerting is in place
- Secrets are not hardcoded
- Resource limits are defined
- Backup/restore is verified

### Database Design

**Add these checks:**
- Indexes support query patterns
- Constraints enforce invariants
- Migrations are idempotent
- Data retention is considered
- Backup strategy is documented

### Machine Learning/Data Science

**Add these checks:**
- Data splits are appropriate
- Evaluation metrics are meaningful
- Model artifacts are versioned
- Reproducibility is ensured
- Resource usage is monitored

---

## Quick Reference Card

```
QUALITY CHECK QUICK REFERENCE

BEFORE MERGING:
□ Automated checks pass
□ No prototype artifacts
□ All actions functional
□ Error states explicit
□ Contract adhered to

SCORING (0-2 per dimension):
□ Contract Adherence
□ Architectural Consistency  
□ State Correctness
□ Production Readiness
□ Error Resilience
□ UX Polish
□ Type Safety
□ Static Analyzability
□ Boundary Discipline
□ Maintainability

TARGET: 80% of maximum (17/20)

AUTOMATIC FAIL IF:
✗ Checks fail
✗ Dead code remains
✗ Prototype artifacts present
✗ Duplication introduced
```

---

*This document is designed to be evoked at any time for quality assessment. Keep it accessible and adapt it to your specific domain needs.*
