Recovered Reconstruction Index

Current recovered layers:
- docs/: recovered SRS, runtime findings, decision notes, and validation notes
- app/: recovered FastAPI shell, project APIs, model catalog, job stubs, and role-model checker stubs
- frontend/: recovered control console and role-model checker UI scaffold
- data/: five representative test projects plus empty models directory
- tests/: smoke coverage for the recovered baseline

What is currently reconstructed faithfully from the conversation:
- project_name as the user-facing identity
- unified workflow preferences
- role-model checker concept and workflow
- async/progress-oriented API surface shape
- documentation map and runtime findings structure

What is currently represented as a stub and still needs deeper rebuild or true restore:
- full inference runtime integration
- full orchestrator/compiler implementation
- real persistence database layer beyond manifest/project scaffolding
- complete unit/integration coverage from the original repo
- exact polished frontend behavior from the lost workspace

Recommended rebuild order from this recovered baseline:
1. restore or rebuild persistence/database layer
2. rebuild inference and model registry runtime
3. rebuild orchestrator/compiler path
4. rebuild full role-model checker behavior
5. expand tests before resuming production changes
