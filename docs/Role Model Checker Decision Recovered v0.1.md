# Role Model Checker Decision Recovered v0.1

The role-model checker exists because local model selection turned out to be role-sensitive.

Recovered rationale:

- some models were acceptable for `architect` but not for `sequencer`
- `critic` was significantly slower than other roles
- the system needed a reusable way for users to test candidate models without repeating the original manual troubleshooting process

Recovered workflow:

1. test `architect`
2. test `sequencer`
3. test `drafter`
4. test `critic` last, usually one role at a time

Recovered policy:

- expose recommended role selections
- allow user overrides
- warn when a non-recommended path is used because it may behave unpredictably
