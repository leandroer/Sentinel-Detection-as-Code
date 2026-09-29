# Deployment and promotion

## Prerequisites

- Azure subscription and isolated resource group
- Azure CLI with Bicep support
- Permission to create Log Analytics, Sentinel, and Logic App resources
- Python 3.11 and the development requirements

For a first-time Azure or GitHub Actions setup, follow the complete [Azure and GitHub OIDC bootstrap guide](azure-oidc-bootstrap.md). It covers the Entra application, federated trust, least-privilege resource-group role assignment, GitHub environment variables, first deployment, troubleshooting, and teardown.

## Infrastructure

```bash
az deployment group create \
  --resource-group <resource-group> \
  --template-file infra/main.bicep \
  --parameters infra/parameters/dev.bicepparam
```

## Analytics rules

```bash
./scripts/deploy.sh dev <resource-group> <workspace-name>
```

The package command emits a complete ARM template and manifest under `dist/<environment>/`.

## GitHub configuration

Create `dev`, `test`, and `prod` environments. Require reviewers for production and configure these repository variables:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`
- `SENTINEL_WORKSPACE_NAME`

Use Azure workload identity federation rather than a client secret.

The deployment workflow first deploys `infra/main.bicep`, then deploys the packaged analytics rules. Run **Verify deployed Sentinel content** after the first deployment and use the scheduled drift workflow to identify portal-side changes.

## Rollback

Redeploy the package attached to the previous GitHub release. Rule IDs remain stable, so ARM updates the existing resources. If an urgent rule disable is required, change `enabled` in source, validate, and promote that commit rather than creating permanent portal drift.
