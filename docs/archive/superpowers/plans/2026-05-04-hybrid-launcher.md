# Hybrid Launcher (v1) Implementation Plan

Date: 2026-05-04
Status: Deferred - v2 (Path A single-window launcher shipped as dfff0cb)
Scope: local app launcher behavior (no API endpoint changes)

## Current State (Path A, Shipped)

The single-window launcher (Path A) has been implemented and shipped:

- `start_narrative_core.cmd` (default) — production mode: builds frontend once, runs uvicorn in single window
- `start_narrative_core.cmd --dev` — dev mode: 2 windows with hot-reload (previous behavior)
- `--skip-build` — use existing `frontend/dist/` without rebuilding
- `--host` / `--port` — custom bind address
- Edge cases: npm check, port-in-use detection, dist verification
- Zero new dependencies

This plan (Path B) adds a tray icon launcher (`pythonw` + `pystray` + `Pillow`) for a "click and it works" experience. Deferred until core features are stable.

---

## Execution Rules

1. Execute tasks in strict order `LAUNCH-001` -> `LAUNCH-008`.
2. Do not continue until current task verify command passes.
3. Do not change backend/frontend business logic in launcher tasks.
4. Keep launcher behavior deterministic (same args -> same process actions).

---

## Atomic Task Plan

### LAUNCH-001 Dependency contract

- Goal: ensure launcher dependencies are explicitly declared.
- Files:
  - `pyproject.toml`
- Command outcome:
  - `python -c "import pystray; from PIL import Image; print('OK')"` succeeds in project env.
- Verify:
  - `python -c "import pystray; from PIL import Image; print('OK')"`

### LAUNCH-002 Silent launcher module

- Goal: create `launcher.py` entry with hidden subprocess + tray lifecycle.
- Files:
  - `launcher.py`
- Command outcome:
  - `python -c "import ast, pathlib; ast.parse(pathlib.Path('launcher.py').read_text(encoding='utf-8')); print('Syntax OK')"` succeeds.
- Verify:
  - `python -c "import ast, pathlib; ast.parse(pathlib.Path('launcher.py').read_text(encoding='utf-8')); print('Syntax OK')"`

### LAUNCH-003 Production batch entrypoint

- Goal: add double-click production launcher wrapper.
- Files:
  - `start_narrative.bat`
- Command outcome:
  - `cmd /c start_narrative.bat` starts launcher process path resolution without immediate script errors.
- Verify:
  - `cmd /c start_narrative.bat`

### LAUNCH-004 Dev launcher documentation alignment

- Goal: align existing dev launcher script comments/usage with production launcher split.
- Files:
  - `start_narrative_core.cmd`
  - `AGENTS.md` (startup section only)
- Command outcome:
  - `start_narrative_core.cmd --dev` and production launcher usage are documented consistently.
- Verify:
  - `findstr /n /c:"start_narrative_core.cmd --dev" AGENTS.md`
  - `findstr /n /c:"start_narrative.bat" AGENTS.md`

### LAUNCH-005 Logging and ignore policy

- Goal: route launcher logs to stable file and exclude from git.
- Files:
  - `.gitignore`
  - launcher module if log path constant exists
- Command outcome:
  - `.narrative.log` (or chosen launcher log file) is ignored by git.
- Verify:
  - `& 'C:\\Program Files\\Git\\cmd\\git.exe' check-ignore -v .narrative.log`

### LAUNCH-006 Launcher error-path hardening

- Goal: deterministic user feedback for missing prerequisites.
- Files:
  - `launcher.py`
- Command outcome:
  - Missing frontend dir / missing npm / build fail returns non-zero and user-visible error path.
- Verify:
  - `python -m pytest tests/test_launcher.py -q -p no:cacheprovider`
  - If no test file yet, create it in this task and make command pass.

### LAUNCH-007 Manual runtime verification script

- Goal: encode manual checks into reproducible checklist doc.
- Files:
  - `docs/superpowers/plans/2026-05-04-hybrid-launcher-verification.md`
- Command outcome:
  - Document includes exact steps and expected observations for:
    - tray icon appears
    - browser open works
    - view logs works
    - stop server stops child process
- Verify:
  - `findstr /n /c:"tray icon" docs\\superpowers\\plans\\2026-05-04-hybrid-launcher-verification.md`
  - `findstr /n /c:"stop server" docs\\superpowers\\plans\\2026-05-04-hybrid-launcher-verification.md`

### LAUNCH-008 Final gate

- Goal: merge-safe validation for launcher changes.
- Files:
  - all touched launcher/docs files
- Command outcome:
  - Launcher-related checks and repository quality gates pass.
- Verify:
  - `cd frontend && npm run lint`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run build`
  - `python -m pytest -q -p no:cacheprovider`

---

## Deterministic Behavior Contract

1. Production launcher:
  - single action entry (`start_narrative.bat`)
  - no persistent console window
  - starts backend process once
  - logs to one predictable file path
2. Dev launcher:
  - explicit `--dev` path via `start_narrative_core.cmd`
  - visible terminal workflow remains available
3. Failure behavior:
  - missing prereqs fail fast with explicit message
  - no partial silent hangs

---

## Notes for Local LLM Executor

1. Do not refactor unrelated services or endpoints.
2. Keep write scope to launcher/docs/dependency/test files only.
3. Add tests before behavior hardening when possible.
4. Commit per task or per small cluster (`001-002`, `003-005`, `006-008`) with verify output captured in commit body.
