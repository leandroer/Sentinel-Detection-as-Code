# Detection coverage

| Domain | Rule | Severity | ATT&CK | Scenario test |
|---|---|---:|---|---|
| Identity | Password spray followed by successful sign-in | High | T1110.003, T1078 | Malicious + benign |
| Identity | MFA fatigue followed by successful sign-in | High | T1621, T1078 | Malicious + benign |
| Cloud | Key Vault secret access volume anomaly | High | T1555, T1530 | Malicious + benign |
| Endpoint | Endpoint credential dumping indicators | High | T1003.001 | Malicious + benign |
| AI security | AI agent sensitive data sent to external destination | High | T1048, T1567 | Malicious + benign |

This initial set intentionally favors complete lifecycle examples over rule volume. New rules should add distinct behavioral coverage and the corresponding test contract.
