#!/usr/bin/env python3
from rulelib import rule_paths, scenario_paths, validate_repository


def main() -> int:
    errors = validate_repository()
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validated {len(rule_paths())} rules and {len(scenario_paths())} scenario contracts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
