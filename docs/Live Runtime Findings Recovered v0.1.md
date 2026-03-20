# Live Runtime Findings Recovered v0.1

Recovered findings from the conversation record:

- project identity needed to be promoted from UUID-only to user-facing `project_name`
- `sequencer` quality depended strongly on model choice
- `critic` was the slowest role and benefited from `minimal_context`
- backend async progress endpoints were needed for long-running jobs and role-model checks
- workflow and testing preferences were unified into one source of truth to avoid drift

Recovered recommended role profile:

- `architect`: Qwen-family 32B Q4-level fit
- `sequencer`: Qwen-family 32B Q5-level fit
- `drafter`: Qwen-family Q4 recommendation
- `critic`: Qwen-family Q5 recommendation with `minimal_context`
