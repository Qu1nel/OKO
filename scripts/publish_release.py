"""Publish a GitHub Release once or verify the existing release without overwriting it."""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def validate_existing(release: dict, tag: str, commit: str, notes: str) -> None:
    if release.get("tag_name") != tag or release.get("target_commitish") != commit:
        raise ValueError("Existing release tag/commit differs from the validated release")
    if (release.get("body") or "").replace("\r\n", "\n").strip() != notes.strip():
        raise ValueError("Existing release notes differ from the validated notes")
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Expected an ordinary published release")


def api(method: str, path: str, payload: dict | None = None, *, allow_missing: bool = False) -> dict | None:
    request = urllib.request.Request(
        "https://api.github.com/" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "oko-release",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        error.close()
        if allow_missing and error.code == 404:
            return None
        raise


def publish(repository: str, tag: str, commit: str, notes: str) -> None:
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository) or not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("Invalid release repository/tag")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Release target must be an exact commit SHA")
    base = f"repos/{repository}"
    ref = api("GET", f"{base}/git/ref/tags/{urllib.parse.quote(tag)}")
    if ref is None or ref["object"]["type"] != "tag":
        raise ValueError("Remote release tag must be annotated")
    tagged = api("GET", f"{base}/git/tags/{ref['object']['sha']}")
    if tagged is None or tagged["object"]["type"] != "commit" or tagged["object"]["sha"] != commit:
        raise ValueError("Remote tag no longer points to the validated commit")
    verification = tagged.get("verification") or {}
    if verification.get("verified") is not True:
        raise ValueError(f"Remote tag signature is not verified: {verification.get('reason', 'missing result')}")
    existing = api("GET", f"{base}/releases/tags/{tag}", allow_missing=True)
    if existing is not None:
        validate_existing(existing, tag, commit, notes)
        print("Existing release commit and notes match; no changes needed.")
        return
    created = api(
        "POST",
        f"{base}/releases",
        {"tag_name": tag, "target_commitish": commit, "name": tag, "body": notes, "draft": False, "prerelease": False},
    )
    if created is None:
        raise RuntimeError("GitHub returned no release")
    validate_existing(created, tag, commit, notes)
    print("Created and verified GitHub Release.")


if __name__ == "__main__":
    publish(
        os.environ["GITHUB_REPOSITORY"],
        os.environ["GITHUB_REF_NAME"],
        os.environ["GITHUB_SHA"],
        Path("release-notes.md").read_text(encoding="utf-8"),
    )
