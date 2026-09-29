# Operations and tuning

## Ownership

Assign every production rule a technical owner, an operational owner, a review date, and a service-level objective for triage. Record tenant-specific exceptions outside the reusable base rule when possible.

## Metrics

Track alerts per day, incident conversion rate, true-positive rate, mean time to triage, query execution duration, and ingestion-to-alert latency. A rule that never fires is not automatically healthy; validate it periodically with controlled synthetic events.

## Drift

Treat portal edits as emergency changes. Reconcile them into Git immediately. The scheduled **Detect Sentinel configuration drift** workflow compares deployed rule properties with source control and reports drift without automatically overwriting an active investigation change.

## Thresholds

Start with the documented values, observe them in `dev`, and promote tenant-specific thresholds only with evidence. Prefer separate variants for service identities instead of broad exclusions.
