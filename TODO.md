# TODO

## Restore Readiness

- [ ] Perform a full restore-readiness review of the recovered `F:\Dev\Narrative-Recover` workspace.
- [ ] Audit the reconstructed code and docs for gaps between the recovered baseline and the lost implementation.
- [ ] Record a prioritized list of resume blockers, behavioral gaps, and missing rebuild slices.

## Core Rebuild

- [ ] Rebuild the persistence/database layer beyond the current stubbed baseline.
- [ ] Rebuild the inference/model runtime layer.
- [ ] Rebuild the orchestrator/compiler path.
- [ ] Expand the role-model checker beyond stub behavior.
- [ ] Add broader automated tests beyond `tests/test_recovered_smoke.py`.

## Frontend And Parity

- [ ] Review frontend parity beyond the current recovered UI shell in `frontend/index.html`.
- [ ] Verify docs, SRS notes, and implementation are synchronized.

## Repo Cleanup

- [ ] Decide whether generated role-model checker run reports under `data/role_model_checker_runs` should remain tracked or be ignored going forward.
