#!/usr/bin/env python3
"""Verify that the canonical rule set is deployed to a Sentinel workspace.

This check intentionally reads only Azure resource metadata. It does not create
alerts or modify workspace content.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

from rulelib import load_yaml, rule_paths


API_VERSION = "2023-12-01-preview"


def az_json(*args: str) -> dict[str, Any]:
    command = ["az", *args, "--output", "json"]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Azure CLI command failed")
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify deployed Sentinel analytics rules against source control.")
    parser.add_argument("--subscription-id", required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--workspace-name", required=True)
    args = parser.parse_args()

    endpoint = (
        f"https://management.azure.com/subscriptions/{args.subscription_id}"
        f"/resourceGroups/{args.resource_group}"
        f"/providers/Microsoft.OperationalInsights/workspaces/{args.workspace_name}"
        f"/providers/Microsoft.SecurityInsights/alertRules?api-version={API_VERSION}"
    )
    deployed = az_json("rest", "--method", "get", "--url", endpoint).get("value", [])
    by_name = {item.get("name"): item for item in deployed}
    errors: list[str] = []

    for path in rule_paths():
        source = load_yaml(path)
        deployed_rule = by_name.get(source["id"])
        if not deployed_rule:
            errors.append(f"missing deployed rule: {source['name']} ({source['id']})")
            continue
        properties = deployed_rule.get("properties", {})
        expected = {"displayName": source["name"], "query": source["query"], "severity": source["severity"], "enabled": source["enabled"]}
        for field, value in expected.items():
            if properties.get(field) != value:
                errors.append(f"{source['name']}: deployed {field} differs from source control")
        if deployed_rule.get("kind") != source["kind"]:
            errors.append(f"{source['name']}: deployed kind differs from source control")

    if errors:
        print("Deployment verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Verified {len(rule_paths())} deployed analytics rules in {args.workspace_name}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"Deployment verification could not run: {error}", file=sys.stderr)
        raise SystemExit(2)
