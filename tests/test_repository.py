from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_telemetry  # noqa: E402
from rulelib import load_yaml, rule_paths, scenario_paths, validate_repository  # noqa: E402


class RepositoryContractTests(unittest.TestCase):
    def test_repository_is_valid(self) -> None:
        self.assertEqual([], validate_repository())

    def test_all_scenario_generators_exist(self) -> None:
        declared = {load_yaml(path)["generator"] for path in scenario_paths()}
        self.assertEqual(declared, set(generate_telemetry.GENERATORS))

    def test_generators_emit_malicious_and_benign_events(self) -> None:
        base = generate_telemetry.datetime(2026, 1, 15, 12, 0, tzinfo=generate_telemetry.timezone.utc)
        for name, generator in generate_telemetry.GENERATORS.items():
            with self.subTest(generator=name):
                malicious, benign = generator(base)
                self.assertGreater(len(malicious), 0)
                self.assertGreater(len(benign), 0)
                for event in malicious + benign:
                    self.assertIn("TimeGenerated", event)
                    self.assertNotIn("contoso.com", json.dumps(event).lower())

    def test_expected_alert_contracts(self) -> None:
        for path in scenario_paths():
            scenario = load_yaml(path)
            with self.subTest(scenario=scenario["id"]):
                self.assertEqual(1, scenario["expected"]["alertCount"])
                self.assertEqual(0, scenario["benignControl"]["expectedAlertCount"])
                self.assertTrue(scenario["expected"]["requiredColumns"])

    def test_rule_ids_and_scenarios_are_unique(self) -> None:
        rules = [load_yaml(path) for path in rule_paths()]
        self.assertEqual(len(rules), len({rule["id"] for rule in rules}))
        self.assertEqual(len(rules), len({rule["scenario"] for rule in rules}))

    def test_fixture_writer_uses_json_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "fixture.jsonl"
            generate_telemetry.write_jsonl(target, [{"a": 1}, {"a": 2}])
            self.assertEqual([{"a": 1}, {"a": 2}], [json.loads(line) for line in target.read_text().splitlines()])


if __name__ == "__main__":
    unittest.main()
