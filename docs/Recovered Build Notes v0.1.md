Recovered Build Notes

This F: reconstruction was created because the original D: workspace became unavailable during active recovery.

Rules followed during reconstruction:
- No writes were made back into D:.
- Recovered files were rebuilt only into F:\Dev\Narrative-Recover.
- The rebuilt tree prefers safe stubs over pretending runtime-complete behavior exists.
- Documentation records what is reconstructed versus what remains approximate.

Git recovery note:
- A new git repository was initialized in F:\Dev\Narrative-Recover after reconstruction work began on the safe copy.
- The recovered workspace is now the active source-control root for rebuild work until any original repository data can be safely recovered from D:.
- Local-only artifacts are ignored through the repository .gitignore, including .venv, .pytest_cache, __pycache__, and editable-build egg-info output.

If the original repository is later recovered:
- Compare docs first.
- Preserve any true source recovered from the original repo over conversational reconstructions.
- Merge by module, not by blind folder overwrite.
