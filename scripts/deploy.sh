#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <dev|test|prod> <resource-group> <workspace-name>" >&2
  exit 2
fi

environment="$1"
resource_group="$2"
workspace_name="$3"

case "$environment" in
  dev|test|prod) ;;
  *) echo "Environment must be dev, test, or prod." >&2; exit 2 ;;
esac

python3 scripts/validate.py
python3 scripts/package_rules.py --environment "$environment" --output "dist/$environment"

az deployment group create \
  --name "sentinel-rules-$environment" \
  --resource-group "$resource_group" \
  --template-file "dist/$environment/sentinel-analytics-rules.json" \
  --parameters workspaceName="$workspace_name"
