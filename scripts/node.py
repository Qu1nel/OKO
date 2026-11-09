"""Run the pinned project Node/npm without changing the system installation."""

import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE_VERSION = (ROOT / ".node-version").read_text(encoding="utf-8").strip()
PACKAGE = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
NPM_VERSION = PACKAGE["packageManager"].removeprefix("npm@")


def paths() -> tuple[Path, Path]:
    if not all(re.fullmatch(r"\d+\.\d+\.\d+", version) for version in (NODE_VERSION, NPM_VERSION)):
        raise RuntimeError("Node/npm versions must be exact x.y.z versions.")
    if PACKAGE["engines"] != {"node": NODE_VERSION, "npm": NPM_VERSION}:
        raise RuntimeError("Keep .node-version, packageManager and engines consistent.")
    machine = platform.machine().lower()
    if machine not in {"amd64", "x86_64"} or sys.platform not in {"win32", "linux"}:
        raise RuntimeError("Project bootstrap supports Windows x64 and Linux x64.")
    target = "win-x64" if sys.platform == "win32" else "linux-x64"
    base = ROOT / ".tools" / f"node-v{NODE_VERSION}-{target}"
    node = base / "node.exe" if sys.platform == "win32" else base / "bin" / "node"
    npm = ROOT / ".tools" / f"npm-{NPM_VERSION}" / "bin" / "npm-cli.js"
    return node, npm


def run(arguments: list[str]) -> int:
    if not arguments or arguments[0] not in {"node", "npm"}:
        print("Usage: python scripts/node.py node|npm [arguments]", file=sys.stderr)
        return 2
    node, npm = paths()
    if not node.is_file() or (arguments[0] == "npm" and not npm.is_file()):
        print("Run python scripts/setup_node.py first.", file=sys.stderr)
        return 2
    env = os.environ.copy()
    env["PATH"] = str(node.parent) + os.pathsep + env.get("PATH", "")
    env["npm_config_update_notifier"] = "false"
    command = [str(node)] + ([str(npm)] if arguments[0] == "npm" else []) + arguments[1:]
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
