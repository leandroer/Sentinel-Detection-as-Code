#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rulelib import arm_rule, load_yaml, rule_paths, validate_repository


def main() -> int:
    parser = argparse.ArgumentParser(description="Package Sentinel rule YAML as an ARM template.")
    parser.add_argument("--environment", choices=("dev", "test", "prod"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    errors = validate_repository()
    if errors:
        for error in errors:
            print(error)
        return 1
    rules = [load_yaml(path) for path in rule_paths()]
    if args.environment == "prod":
        for rule in rules:
            rule["enabled"] = True
    template = {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {"workspaceName": {"type": "string"}},
        "variables": {"environment": args.environment},
        "resources": [arm_rule(rule) for rule in rules],
        "outputs": {"ruleCount": {"type": "int", "value": len(rules)}, "environment": {"type": "string", "value": args.environment}},
    }
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / "sentinel-analytics-rules.json"
    target.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    manifest = {"environment": args.environment, "rules": [{"id": item["id"], "name": item["name"], "scenario": item["scenario"]} for item in rules]}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Packaged {len(rules)} rules for {args.environment} in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
