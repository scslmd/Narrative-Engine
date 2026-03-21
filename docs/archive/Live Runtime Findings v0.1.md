# Live Runtime Findings v0.1

Current runtime findings:

- DeepSeek 32B Q4 performed acceptably for `architect`.
- `sequencer` was stronger on `qwen2.5-32b-instruct-q5_k_m`.
- `drafter` performed better on `qwen2.5-32b-instruct-q4_k_m`.
- `critic` remained the slowest role in testing.
- `minimal_context` is the preferred critic profile for current workflow tuning.

Recommended operating stance:

- treat model-role selection as empirical, not fixed
- A/B test meaningful changes before promoting them
- write model-selection decisions back into docs and the SRS
