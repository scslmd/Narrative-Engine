# Code Optimization TODO - Validated Checklist

Generated: 2026-03-28

This checklist keeps only the items that are supported by the current implementation in
`app/services/story_knowledge.py` and related persistence code.

It intentionally excludes speculative changes that are not justified by the current code review.

## Priority 1 - Correctness Under Concurrency

### 1. Harden comparison ID generation

**Location**: `app/services/story_knowledge.py:196-197`

**Current code**

```python
comparison_id = self._comparison_id(
    normalized_project_id,
    len(self.repository.list_arc_comparisons(normalized_project_id)) + 1,
)
```

**Why this matters**

- The next ID is derived from the current row count.
- Two concurrent requests can compute the same `comparison_id`.
- The repository write path uses `ON CONFLICT(comparison_id) DO UPDATE`, so the failure mode is silent overwrite, not a clean create failure.

**Required fix**

- Replace count-based ID generation with a collision-safe strategy.
- Keep the existing feature behavior intact: one stored comparison record per request.
- Do not change the comparison schema or ranking logic as part of this fix.

**Definition of done**

- Two overlapping comparison requests for the same project cannot resolve to the same `comparison_id`.
- A later request cannot overwrite a peer request solely because both read the same list length.

---

### 2. Harden selection ID generation

**Location**: `app/services/story_knowledge.py:251-255`

**Current code**

```python
selection_id = self._selection_id(
    normalized_project_id,
    len(self.repository.list_arc_selections(normalized_project_id)) + 1,
)
```

**Why this matters**

- The next selection ID is also derived from a non-atomic count.
- The persistence layer uses `ON CONFLICT(selection_id) DO UPDATE`.
- Concurrent requests can collapse into one logical selection record.

**Required fix**

- Replace count-based `selection_id` generation with a collision-safe strategy.
- Preserve current selection semantics, decision recording, and response shape.
- Do not change stage-map or comparison-link behavior unless required by the ID fix.

**Definition of done**

- Two overlapping selection requests for the same project cannot produce the same `selection_id`.
- A concurrent request cannot overwrite another selection record because both computed the same next index.

---

## Priority 2 - Proven N+1 Read Pattern

### 3. Remove per-character relationship queries from character listing

**Location**:

- `app/services/story_knowledge.py:331-335`
- `app/services/story_knowledge.py:582-585`

**Current pattern**

`list_character_profiles()` iterates all character records, and `_character_profile_from_record()` performs:

```python
self.repository.list_relationship_edges_for_character(record.project_id, record.character_id)
```

for each character.

**Why this matters**

- `GET /characters` becomes one character list query plus one relationship query per character.
- This is a real N+1 pattern and will scale poorly as the cast grows.

**Required fix**

- Batch-load relationship edges for the project once, or otherwise avoid one query per character during list projection.
- Keep `get_character_profile()` behavior unchanged unless the shared implementation makes that change necessary.
- Preserve `CharacterProfile.relationship_edges` in the response.

**Definition of done**

- Listing N characters no longer performs N additional relationship-edge queries.
- Returned character payloads still include correct `relationship_edges`.

---

## Not Currently Justified

These items were reviewed and should not be treated as active optimization work without new evidence:

### `_comparison_notes_for_arc()`

**Location**: `app/services/story_knowledge.py:511-518`

- This is a linear scan, but there is no current evidence that it is a meaningful hotspot.
- Do not optimize it ahead of the three items above.

### `_unique_strings()`

**Location**: `app/services/story_knowledge.py:784-791`

- This is standard ordered de-duplication logic.
- Replacing it with `set()` would change ordering behavior.
- Replacing it with `dict.fromkeys()` would be stylistic, not a meaningful optimization on its own.

### Generic "N+1 pattern" hits in the earlier draft

- Several previously listed entries were just loops over already-fetched records, not additional database queries.
- Treat only the character-list relationship fetch as a validated N+1 issue for now.

### Connection pooling / query logging / transaction-isolation changes

- These may be useful later, but this review did not find enough evidence to make them part of the immediate optimization backlog.
- Do not add them as part of the bounded fixes above.

---

## Recommended Execution Order

1. Fix comparison ID generation.
2. Fix selection ID generation.
3. Batch relationship loading for character lists.

---

## Guardrails

- Do not refactor unrelated story-knowledge logic while addressing these items.
- Do not change response schemas unless the bounded fix requires it.
- Do not introduce new persistence features beyond what is necessary to make the identified paths safe and efficient.
- Validate any concurrency fix against the existing repository upsert behavior before widening scope.
