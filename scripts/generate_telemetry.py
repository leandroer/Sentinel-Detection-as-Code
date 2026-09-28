#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from rulelib import load_yaml, scenario_paths


def timestamp(base: datetime, minutes: int) -> str:
    return (base + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def password_spray_success(base: datetime) -> tuple[list[dict], list[dict]]:
    malicious = [
        {"TimeGenerated": timestamp(base, i), "UserPrincipalName": "target.user@example.invalid", "IPAddress": f"192.0.2.{10 + i % 4}", "ResultType": 50126, "ResultDescription": "Invalid username or password", "AppDisplayName": "Microsoft 365"}
        for i in range(9)
    ]
    malicious.append({"TimeGenerated": timestamp(base, 10), "UserPrincipalName": "target.user@example.invalid", "IPAddress": "198.51.100.42", "ResultType": 0, "ResultDescription": "Success", "AppDisplayName": "Microsoft 365"})
    benign = [{"TimeGenerated": timestamp(base, i), "UserPrincipalName": "test.user@example.invalid", "IPAddress": "192.0.2.20", "ResultType": 50126, "ResultDescription": "Invalid username or password", "AppDisplayName": "Microsoft 365"} for i in range(4)]
    return malicious, benign


def mfa_fatigue_success(base: datetime) -> tuple[list[dict], list[dict]]:
    malicious = [{"TimeGenerated": timestamp(base, i), "UserPrincipalName": "fatigued.user@example.invalid", "IPAddress": "203.0.113.21", "ResultType": 500121, "ResultDescription": "MFA denied; user declined", "AppDisplayName": "Azure Portal"} for i in range(5)]
    malicious.append({"TimeGenerated": timestamp(base, 6), "UserPrincipalName": "fatigued.user@example.invalid", "IPAddress": "203.0.113.21", "ResultType": 0, "ResultDescription": "Success", "AppDisplayName": "Azure Portal"})
    benign = [{"TimeGenerated": timestamp(base, i), "UserPrincipalName": "training.user@example.invalid", "IPAddress": "192.0.2.30", "ResultType": 500121, "ResultDescription": "MFA denied; user declined", "AppDisplayName": "Azure Portal"} for i in range(2)]
    return malicious, benign


def key_vault_access_anomaly(base: datetime) -> tuple[list[dict], list[dict]]:
    common = {"ResourceProvider": "MICROSOFT.KEYVAULT", "OperationName": "SecretGet", "ResultType": "Success", "identity_claim_oid_g": "11111111-1111-4111-8111-111111111111", "callerIpAddress_s": "198.51.100.60", "Resource": "kv-lab-detection"}
    malicious = [dict(common, TimeGenerated=timestamp(base, i // 3), requestUri_s=f"https://kv-lab-detection.vault.azure.net/secrets/secret-{i}") for i in range(22)]
    benign = [dict(common, TimeGenerated=timestamp(base, i), identity_claim_oid_g="22222222-2222-4222-8222-222222222222", requestUri_s=f"https://kv-lab-detection.vault.azure.net/secrets/routine-{i}") for i in range(5)]
    return malicious, benign


def endpoint_credential_dumping(base: datetime) -> tuple[list[dict], list[dict]]:
    common = {"TimeGenerated": timestamp(base, 0), "DeviceName": "lab-endpoint-01", "AccountUpn": "analyst@example.invalid", "InitiatingProcessFileName": "powershell.exe", "InitiatingProcessAccountUpn": "analyst@example.invalid", "SHA256": "0" * 64}
    malicious = [dict(common, FileName="procdump.exe", ProcessCommandLine="procdump.exe -ma lsass.exe C:\\Lab\\lsass.dmp")]
    benign = [dict(common, FileName="procdump.exe", ProcessCommandLine="procdump.exe -ma sample-app.exe C:\\Lab\\sample.dmp")]
    return malicious, benign


def ai_agent_data_exfiltration(base: datetime) -> tuple[list[dict], list[dict]]:
    common = {"TimeGenerated": timestamp(base, 0), "UserPrincipalName_s": "analyst@example.invalid", "ApplicationName_s": "Research Agent", "AgentId_s": "agent-lab-001", "CorrelationId_g": "33333333-3333-4333-8333-333333333333"}
    malicious = [dict(common, Destination_s="external@outside.test", SensitivityClassification_s="Restricted", OutputBytes_d=16384)]
    benign = [dict(common, Destination_s="security@example.invalid", SensitivityClassification_s="Public", OutputBytes_d=1024)]
    return malicious, benign


GENERATORS: dict[str, Callable[[datetime], tuple[list[dict], list[dict]]]] = {
    "password_spray_success": password_spray_success,
    "mfa_fatigue_success": mfa_fatigue_success,
    "key_vault_access_anomaly": key_vault_access_anomaly,
    "endpoint_credential_dumping": endpoint_credential_dumping,
    "ai_agent_data_exfiltration": ai_agent_data_exfiltration,
}


def write_jsonl(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate safe synthetic telemetry fixtures.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--scenario")
    parser.add_argument("--output", type=Path, default=Path("build/telemetry"))
    args = parser.parse_args()
    base = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    manifests = [load_yaml(path) for path in scenario_paths()]
    if args.scenario:
        manifests = [item for item in manifests if item["id"] == args.scenario]
        if not manifests:
            parser.error(f"unknown scenario: {args.scenario}")
    for manifest in manifests:
        malicious, benign = GENERATORS[manifest["generator"]](base)
        write_jsonl(args.output / f"{manifest['id']}.malicious.jsonl", malicious)
        write_jsonl(args.output / f"{manifest['id']}.benign.jsonl", benign)
        print(f"Generated {manifest['id']}: {len(malicious)} malicious, {len(benign)} benign events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
