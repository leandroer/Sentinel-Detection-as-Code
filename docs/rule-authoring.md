# Rule authoring guide

Each analytics rule must include:

- Stable UUID and descriptive name
- Explicit query frequency and lookback period
- Time filtering in KQL
- MITRE ATT&CK tactics and techniques
- At least one entity mapping
- Incident grouping behavior
- Suppression configuration
- Practical tuning guidance
- A matching scenario contract

Use projected column names in entity mappings and custom details. Avoid tenant-specific IDs, workspace functions, or watchlist names unless the dependency is documented.

## Review checklist

1. Does the query detect a behavior rather than a single fragile indicator?
2. Can an analyst understand why it fired from the projected columns?
3. Are thresholds justified and configurable?
4. Does the benign control exercise the closest non-malicious behavior?
5. Are service accounts, scanners, and administrative tooling considered?
6. Is the grouping key stable enough to prevent incident flooding?
