"""Validate a proposed release and extract its changelog notes."""

import argparse
import datetime
import json
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate_tag(root: Path, tag: str) -> None:
    ref = f"refs/tags/{tag}"
    kind = subprocess.check_output(["git", "cat-file", "-t", ref], cwd=root, text=True).strip()
    if kind != "tag":
        raise ValueError("Release requires an annotated tag; sign it in the local release procedure")
    target = subprocess.check_output(["git", "rev-parse", f"{ref}^{{commit}}"], cwd=root, text=True).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if target != head:
        raise ValueError("Release tag must point to the checked out commit")
    signature = subprocess.run(["git", "verify-tag", ref], cwd=root, text=True, capture_output=True, check=False)
    if signature.returncode != 0:
        raise ValueError("Tag signature could not be verified: " + signature.stderr.strip())


def release_notes(root: Path, tag: str) -> str:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version) or tag != f"v{version}":
        raise ValueError(f"Expected tag v{version}, got {tag}")
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
    uv_lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    own = [item["version"] for item in uv_lock["package"] if item["name"] == project["project"]["name"]]
    if own != [version] or package["version"] != version or lock["version"] != version:
        raise ValueError("Project versions disagree in manifests/lock files")
    if lock["packages"][""]["version"] != version:
        raise ValueError("npm root package version disagrees")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    pattern = rf"^## \[{re.escape(version)}\] - (\d{{4}}-\d{{2}}-\d{{2}})\s*$\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, changelog, re.MULTILINE | re.DOTALL)
    if not match or not match[2].strip():
        raise ValueError(f"Missing dated, nonempty CHANGELOG entry [{version}]")
    date = datetime.date.fromisoformat(match[1])
    if date > datetime.datetime.now(datetime.UTC).date():
        raise ValueError("Release date is in the future")
    return match[2].strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--require-tag", action="store_true")
    parser.add_argument("--notes-file", type=Path)
    args = parser.parse_args()
    try:
        notes = release_notes(ROOT, args.tag)
    except ValueError as error:
        parser.error(str(error))
    if args.require_tag:
        try:
            validate_tag(ROOT, args.tag)
        except ValueError as error:
            parser.error(str(error))
    if args.notes_file:
        args.notes_file.write_text(notes, encoding="utf-8")
    else:
        print(notes, end="")


if __name__ == "__main__":
    main()
