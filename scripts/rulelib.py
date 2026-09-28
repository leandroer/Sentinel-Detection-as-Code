from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
RULE_ROOT = ROOT / "analytics-rules"
SCENARIO_ROOT = ROOT / "scenarios"

REQUIRED_RULE_FIELDS = {
    "id", "name", "description", "status", "severity", "kind", "enabled",
    "queryFrequency", "queryPeriod", "triggerOperator", "triggerThreshold",
    "tactics", "techniques", "dataSources", "entityMappings", "query",
    "incidentConfiguration", "tuning", "scenario",
}
SEVERITIES = {"Informational", "Low", "Medium", "High"}
TACTICS = {
    "Reconnaissance", "ResourceDevelopment", "InitialAccess", "Execution",
    "Persistence", "PrivilegeEscalation", "DefenseEvasion", "CredentialAccess",
    "Discovery", "LateralMovement", "Collection", "CommandAndControl",
    "Exfiltration", "Impact",
}
ISO_DURATION = re.compile(r"^P(?=\d|T\d)(?:\d+D)?(?:T(?:\d+H)?(?:\d+M)?(?:\d+S)?)?$")
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return value


def rule_paths() -> list[Path]:
    return sorted(RULE_ROOT.glob("**/*.yaml"))


def scenario_paths() -> list[Path]:
    return sorted(SCENARIO_ROOT.glob("*/scenario.yaml"))


def validate_rule(path: Path, rule: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_RULE_FIELDS - rule.keys()
    if missing:
        errors.append(f"missing fields: {', '.join(sorted(missing))}")
    if not UUID.match(str(rule.get("id", ""))):
        errors.append("id must be a UUID")
    if rule.get("severity") not in SEVERITIES:
        errors.append(f"unsupported severity: {rule.get('severity')}")
    unknown_tactics = set(rule.get("tactics", [])) - TACTICS
    if unknown_tactics:
        errors.append(f"unsupported tactics: {', '.join(sorted(unknown_tactics))}")
    for field in ("queryFrequency", "queryPeriod", "suppressionDuration"):
        value = rule.get(field)
        if value is not None and not ISO_DURATION.match(str(value)):
            errors.append(f"{field} is not an ISO 8601 duration")
    query = str(rule.get("query", ""))
    if len(query.strip().splitlines()) < 3:
        errors.append("query must contain at least three lines")
    if "TimeGenerated" not in query:
        errors.append("query must explicitly constrain TimeGenerated")
    if not rule.get("entityMappings"):
        errors.append("at least one entity mapping is required")
    if not rule.get("techniques"):
        errors.append("at least one ATT&CK technique is required")
    if not rule.get("tuning"):
        errors.append("at least one tuning note is required")
    return [f"{path.relative_to(ROOT)}: {error}" for error in errors]


def validate_repository() -> list[str]:
    errors: list[str] = []
    rules: dict[str, tuple[Path, dict[str, Any]]] = {}
    ids: dict[str, Path] = {}
    for path in rule_paths():
        rule = load_yaml(path)
        errors.extend(validate_rule(path, rule))
        scenario_id = str(rule.get("scenario", ""))
        if scenario_id in rules:
            errors.append(f"{path.relative_to(ROOT)}: duplicate scenario reference {scenario_id}")
        rules[scenario_id] = (path, rule)
        rule_id = str(rule.get("id", ""))
        if rule_id in ids:
            errors.append(f"{path.relative_to(ROOT)}: duplicate rule id also used by {ids[rule_id].relative_to(ROOT)}")
        ids[rule_id] = path

    scenarios: dict[str, Path] = {}
    for path in scenario_paths():
        scenario = load_yaml(path)
        scenario_id = str(scenario.get("id", ""))
        scenarios[scenario_id] = path
        referenced_rule = ROOT / str(scenario.get("rule", ""))
        if not referenced_rule.is_file():
            errors.append(f"{path.relative_to(ROOT)}: referenced rule does not exist")
        if scenario_id not in rules:
            errors.append(f"{path.relative_to(ROOT)}: no rule references this scenario")
        for field in ("table", "generator", "expected", "benignControl"):
            if field not in scenario:
                errors.append(f"{path.relative_to(ROOT)}: missing {field}")

    missing_scenarios = set(rules) - set(scenarios)
    for scenario_id in sorted(missing_scenarios):
        path, _ = rules[scenario_id]
        errors.append(f"{path.relative_to(ROOT)}: scenario {scenario_id} does not exist")
    if len(rules) != 5:
        errors.append(f"repository contract expects 5 rules; found {len(rules)}")
    return errors


def arm_rule(rule: dict[str, Any], workspace_name: str = "[parameters('workspaceName')]") -> dict[str, Any]:
    properties = {
        key: rule[key]
        for key in (
            "displayName", "description", "severity", "enabled", "query",
            "queryFrequency", "queryPeriod", "triggerOperator", "triggerThreshold",
            "suppressionDuration", "suppressionEnabled", "tactics", "techniques",
            "subTechniques",
            "entityMappings", "customDetails", "incidentConfiguration",
        )
        if key in rule
    }
    properties["displayName"] = rule["name"]
    return {
        "type": "Microsoft.OperationalInsights/workspaces/providers/alertRules",
        "apiVersion": "2023-12-01-preview",
        "name": f"[format('{{0}}/Microsoft.SecurityInsights/{{1}}', parameters('workspaceName'), '{rule['id']}')]",
        "kind": rule["kind"],
        "properties": properties,
    }
