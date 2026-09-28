# Contributing

Contributions should preserve the rule-to-scenario contract.

1. Create one YAML rule in `analytics-rules/<domain>/`.
2. Create a matching scenario directory under `scenarios/`.
3. Include at least one malicious and one benign fixture.
4. Document tuning, prerequisites, and investigation steps.
5. Run `python scripts/validate.py` and the unit tests.

Do not include customer telemetry, credentials, tenant identifiers, or weaponized attack code. Generated identifiers must use the reserved `example.invalid` domain.
