# Testing model

Testing occurs at three levels.

## Static contract tests

`scripts/validate.py` checks required metadata, UUID uniqueness, ISO durations, ATT&CK tactics, time constraints, entity mappings, and one-to-one rule/scenario relationships.

## Synthetic fixture tests

`scripts/generate_telemetry.py` produces deterministic malicious and benign JSONL fixtures. Unit tests verify event counts, reserved identifiers, and generator completeness.

## Workspace integration tests

For a real test workspace:

1. Deploy infrastructure and rules to `test`.
2. Ingest generated fixtures using an approved Logs Ingestion API pipeline.
3. Wait for the rule frequency plus ingestion latency.
4. Query `SecurityAlert` and `SecurityIncident` using the rule UUID.
5. Assert the alert count and entity values declared in `scenario.yaml`.
6. Remove test data or let the test workspace retention policy expire it.

The repository intentionally does not embed tenant credentials or automatically ingest data from an untrusted pull request.

### Native-table constraint

`SigninLogs`, `AzureDiagnostics`, and `DeviceProcessEvents` are connector-owned tables. The Azure Logs Ingestion API cannot insert arbitrary fixtures into them, so a workflow must not claim to create end-to-end alerts from JSONL alone. Validate those rules in an isolated test tenant by generating controlled, authorized activity through the relevant identity, Azure, and endpoint test paths. For custom tables such as `AIApp_CL`, use a dedicated DCR/DCE test pipeline and validate alerts after ingestion.

The repository's **Verify deployed Sentinel content** workflow verifies that the source-controlled rule properties are deployed correctly. It is a deployment integration check, not a substitute for connector-specific behavior validation.
