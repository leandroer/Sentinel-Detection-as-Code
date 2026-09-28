# Scenario contracts

Every analytics rule must reference exactly one scenario. A scenario declares its source table, generator, expected entities, projected result columns, and a benign control.

The generator emits two JSONL files:

- `<scenario>.malicious.jsonl` contains synthetic events expected to match.
- `<scenario>.benign.jsonl` contains synthetic events expected not to match.

These fixtures test content structure and thresholds; they are not a substitute for running KQL against a test Log Analytics workspace. The deployment workflow supports that integration test as an environment-gated step.
