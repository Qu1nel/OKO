"""Check the staged files exposed by pre-commit without modifying them."""

import subprocess
import sys
from pathlib import Path
from platform import python_version

ROOT = Path(__file__).resolve().parents[1]


def main(arguments: list[str]) -> int:
    if len(arguments) < 2 or arguments[0] not in {"lint", "format", "frontend"}:
        return 2
    expected_version = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve() or python_version() != expected_version:
        print("Checks require the project .venv created by uv sync --locked.", file=sys.stderr)
        return 2
    mode, *files = arguments
    files = [str(Path(filename).resolve()) for filename in files]
    if mode == "frontend":
        command = [sys.executable, str(ROOT / "scripts" / "node.py"), "node"]
        command += [str(ROOT / "node_modules" / "prettier" / "bin" / "prettier.cjs"), "--check"]
    else:
        python = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        if not python.is_file():
            print("Run uv sync --locked before committing.", file=sys.stderr)
            return 2
        command = [str(python), "-m", "ruff", "check" if mode == "lint" else "format"]
        if mode == "format":
            command.append("--check")
    return subprocess.run(command + ["--", *files], cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
