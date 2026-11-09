"""Run the same project checks locally and in CI without modifying files."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS: dict[str, list[str]] = {
    "python-lint": ["-m", "ruff", "check", "."],
    "python-format": ["-m", "ruff", "format", "--check", "."],
    "python-types": ["-m", "ty", "check"],
    "python-tests": ["-m", "unittest", "discover", "-s", "tests", "-v"],
    "frontend-types": ["scripts/node.py", "npm", "run", "check:types"],
    "frontend-format": ["scripts/node.py", "npm", "run", "check:format"],
    "frontend-build": ["scripts/node.py", "npm", "run", "build"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        action="append",
        choices=["python", "frontend", *CHECKS],
        help="Select a group or one check; repeat to select several (default: all)",
    )
    selected = parser.parse_args().only
    results: dict[str, int] = {}
    for name, arguments in CHECKS.items():
        if selected and name not in selected and name.split("-", 1)[0] not in selected:
            continue
        print(f"\n[{name}]", flush=True)
        results[name] = subprocess.run([sys.executable, *arguments], cwd=ROOT, check=False).returncode

    print("\n" + ", ".join(f"{name}: {'PASS' if code == 0 else 'FAIL'}" for name, code in results.items()))
    return int(any(results.values()))


if __name__ == "__main__":
    raise SystemExit(main())
