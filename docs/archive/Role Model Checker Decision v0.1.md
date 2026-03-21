# Role Model Checker Decision v0.1

Rationale:

- local model behavior varies by role
- the project needs a repeatable way to compare candidates
- model substitutions should be validated before becoming defaults

Workflow:

- select candidate models per role
- run the checker against architect, sequencer, drafter, and critic
- inspect pass/fail outcomes, warnings, findings, and report output
- update documented defaults only after comparative validation

Policy:

- treat checker results as decision support, not marketing copy
- keep recommended selections aligned with documented runtime findings
- validate role-specific changes before promoting them into the workflow defaults
