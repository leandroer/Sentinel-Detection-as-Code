# Architecture

The repository separates authoring, packaging, and deployment so the same reviewed content moves between environments without manual portal edits.

```mermaid
flowchart TB
    subgraph Source["Source control"]
      R["Rule YAML"]
      S["Scenario contract"]
      G["Telemetry generator"]
    end
    subgraph CI["Pull request validation"]
      V["Schema and relationship checks"]
      U["Unit tests"]
      P["ARM package build"]
    end
    subgraph Azure["Isolated Azure environment"]
      L["Log Analytics"]
      M["Microsoft Sentinel"]
      A["Analytics rules"]
      I["Incidents"]
      W["Logic App playbooks"]
    end
    R --> V
    S --> V
    G --> U
    V --> P
    U --> P
    P --> A
    G --> L
    L --> M --> A --> I --> W
```

## Trust boundaries

- Pull-request jobs do not receive Azure credentials.
- Deployment uses GitHub environment approval and federated identity.
- Synthetic data contains reserved documentation domains and addresses.
- Playbooks deploy in simulation mode and have no destructive connector actions.
- Production thresholds are reviewed in source control.

## Content ownership

Rule YAML is canonical. Generated ARM templates are disposable release artifacts. Editing a rule in the Sentinel portal creates drift and should be reconciled back into source control or overwritten by the next deployment.
