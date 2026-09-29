# Azure and GitHub OIDC bootstrap

This guide prepares a blank Azure subscription and GitHub repository for passwordless deployment. It creates no client secret. GitHub Actions obtains a short-lived token only when the workflow runs from the named GitHub environment.

Use a dedicated, non-production resource group for the first deployment. The example values below are safe placeholders; replace them before running commands.

## Prerequisites and permissions

Install the current [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) and sign in:

```bash
az login
az account set --subscription "<subscription-id-or-name>"
```

The person completing the bootstrap needs:

- Permission to create an Entra application and service principal, or help from an Entra administrator.
- `Owner` or `User Access Administrator` at the target resource-group scope to create the role assignment.
- Permission to create the target resource group. `Contributor` is sufficient after the role assignment exists.

The GitHub deployment identity receives `Contributor` only on the dedicated resource group. Do not grant it subscription-wide access.

## 1. Create the resource group and register providers

```bash
export SUBSCRIPTION_ID="<subscription-id>"
export LOCATION="eastus"
export RESOURCE_GROUP="rg-sentinel-detection-dev"

az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

for provider in Microsoft.OperationalInsights Microsoft.OperationsManagement Microsoft.SecurityInsights Microsoft.Logic; do
  az provider register --namespace "$provider"
done
```

Provider registration can take several minutes. Check that each provider is registered before the first deployment:

```bash
az provider show --namespace Microsoft.SecurityInsights --query registrationState --output tsv
```

## 2. Create a dedicated Entra application

```bash
export APP_NAME="github-sentinel-detection-as-code"
export TENANT_ID="$(az account show --query tenantId --output tsv)"

export AZURE_CLIENT_ID="$(az ad app create --display-name "$APP_NAME" --query appId --output tsv)"
export SERVICE_PRINCIPAL_OBJECT_ID="$(az ad sp create --id "$AZURE_CLIENT_ID" --query id --output tsv)"
```

Assign the application the minimum broad role needed to deploy this lab. For a production implementation, replace `Contributor` with a reviewed custom role limited to the resource types in `infra/` and the packaged Sentinel rule template.

```bash
export RESOURCE_GROUP_SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"

az role assignment create \
  --assignee-object-id "$SERVICE_PRINCIPAL_OBJECT_ID" \
  --assignee-principal-type ServicePrincipal \
  --role Contributor \
  --scope "$RESOURCE_GROUP_SCOPE"
```

## 3. Trust the GitHub environment with OIDC

The deployment workflow targets GitHub environments named `dev`, `test`, and `prod`. Create one federated credential per environment that you intend to use. The subject must exactly match the GitHub repository and environment name.

Create `credential-dev.json` outside the repository or remove it after use:

```json
{
  "name": "github-sentinel-detection-dev",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:leandroer/Sentinel-Detection-as-Code:environment:dev",
  "description": "Allows the dev GitHub environment to deploy Sentinel Detection as Code.",
  "audiences": ["api://AzureADTokenExchange"]
}
```

Create the credential:

```bash
az ad app federated-credential create \
  --id "$AZURE_CLIENT_ID" \
  --parameters credential-dev.json
```

For `test` or `prod`, copy the file and change both `name` and the final environment segment of `subject`. Never use a broad branch-based credential when environment protection rules provide the intended control boundary.

Verify the trust configuration:

```bash
az ad app federated-credential list --id "$AZURE_CLIENT_ID" --output table
```

## 4. Configure the GitHub environment

In the repository, open **Settings → Environments → New environment** and create `dev`.

Under **Environment variables**, add these values. They are identifiers, not secrets, and the deployment workflow reads them using GitHub `vars`.

| Variable | Value |
|---|---|
| `AZURE_CLIENT_ID` | `$AZURE_CLIENT_ID` from step 2 |
| `AZURE_TENANT_ID` | `$TENANT_ID` from step 2 |
| `AZURE_SUBSCRIPTION_ID` | `$SUBSCRIPTION_ID` from step 1 |
| `AZURE_RESOURCE_GROUP` | `$RESOURCE_GROUP` from step 1 |
| `SENTINEL_WORKSPACE_NAME` | `law-sentinel-detection-dev`, or your chosen name |

Keep `dev` unprotected while validating the lab. Create `test` and `prod` separately, use distinct resource groups and identities where practical, and require reviewers for `prod`.

## 5. Run the first deployment

1. Open **Actions → Deploy Sentinel content → Run workflow**.
2. Select `dev`.
3. Review the workflow output: it validates the repository, packages the rules, authenticates with OIDC, and deploys the ARM template.
4. In Azure, confirm the Log Analytics workspace, Sentinel solution, two Logic Apps, and five analytics rules exist.

You can also deploy from a trusted local Azure CLI session:

```bash
az deployment group create \
  --name sentinel-lab-dev \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/main.bicep \
  --parameters infra/parameters/dev.bicepparam

./scripts/deploy.sh dev "$RESOURCE_GROUP" "law-sentinel-detection-dev"
```

## Troubleshooting

| Symptom | Likely cause | Resolution |
|---|---|---|
| `No subscriptions found` or role-assignment failure | Insufficient bootstrap permission | Ask a subscription owner or User Access Administrator to create the scoped assignment. |
| `AADSTS70021` during `azure/login` | Federated subject, issuer, or audience does not match | Compare the environment name and repository casing with the credential JSON. |
| `Missing environment variable` | GitHub variable was created at repository rather than environment scope, or typo | Add the value under the selected environment's variables. |
| Resource provider is not registered | Subscription provider registration has not completed | Register the provider and wait for `Registered`. |
| Sentinel rule deployment fails | Workspace or Sentinel solution is not ready | Deploy `infra/main.bicep` first, wait for completion, then rerun the content deployment. |

## Teardown

For a lab, delete the resource group to remove deployed Azure resources:

```bash
az group delete --name "$RESOURCE_GROUP" --yes --no-wait
```

Then remove the federated credential, service principal, and application if they are dedicated to this lab. Confirm the application is not shared before deleting it:

```bash
az ad app federated-credential delete --id "$AZURE_CLIENT_ID" --federated-credential-id github-sentinel-detection-dev
az ad sp delete --id "$AZURE_CLIENT_ID"
az ad app delete --id "$AZURE_CLIENT_ID"
```

## References

- [Authenticate to Azure from GitHub Actions by OpenID Connect](https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect)
- [Create a Microsoft Entra federated identity credential](https://learn.microsoft.com/entra/workload-id/workload-identity-federation-create-trust)
- [Azure CLI: `az ad app federated-credential`](https://learn.microsoft.com/cli/azure/ad/app/federated-credential)
