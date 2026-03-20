Recovered Validation Notes

Quick checks:
1. Create a Python 3.12 virtual environment in this recovered folder.
2. Install dependencies with `pip install -e .[dev]`.
3. Run `python -m pytest tests/test_recovered_smoke.py -q`.
4. Launch the app with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
5. Open `http://127.0.0.1:8000/role-model-checker-ui`.

Current status:
- This recovered tree is a safe reconstruction baseline.
- It is not a byte-perfect restore of the lost D: repository.
- Runtime LLM integration is still represented as recovered stubs until the original implementation is either recovered or rebuilt.
