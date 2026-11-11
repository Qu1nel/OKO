"""Test hooks without Python on PATH and preserve partially staged changes."""

import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def setUpModule():
    (ROOT / ".work").mkdir(exist_ok=True)


def executable(name: str) -> str:
    result = shutil.which(name)
    if result is None:
        raise RuntimeError(f"Required tool not found: {name}")
    return result


class PrecommitTests(unittest.TestCase):
    def test_staged_snapshot_without_python_on_path(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".work", prefix="precommit-regression-") as temporary:
            fixture = Path(temporary)
            env = os.environ.copy()
            env.pop("VIRTUAL_ENV", None)
            env.pop("UV_PROJECT_ENVIRONMENT", None)
            env.update(
                PRE_COMMIT_HOME=str(ROOT / ".work/pre-commit-cache"),
                UV_CACHE_DIR=str(ROOT / ".work/uv-cache"),
                GIT_CONFIG_COUNT="1",
                GIT_CONFIG_KEY_0="safe.directory",
                GIT_CONFIG_VALUE_0=fixture.as_posix(),
            )
            tools = {name: executable(name) for name in ("uv", "git")}
            if sys.platform == "win32":
                env["PATH"] = os.pathsep.join(
                    [
                        str(Path(tools["uv"]).parent),
                        str(Path(tools["git"]).parent),
                        str(Path(os.environ["SystemRoot"]) / "System32"),
                    ]
                )
            else:
                tools.update({name: executable(name) for name in ("bash", "dirname")})
                binary = fixture / "bin"
                binary.mkdir()
                for name, target in tools.items():
                    if target:
                        wrapper = binary / name
                        wrapper.write_text(f'#!/bin/sh\nexec {shlex.quote(target)} "$@"\n', encoding="utf-8")
                        wrapper.chmod(0o755)
                env["PATH"] = str(binary)
            self.assertIsNone(shutil.which("python", path=env["PATH"]))
            config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
            config["repos"][0]["hooks"] = config["repos"][0]["hooks"][:2]
            for hook in config["repos"][0]["hooks"]:
                parts = shlex.split(hook["entry"])
                parts[parts.index("--python") + 1] = str(ROOT / ".venv")
                parts[parts.index("scripts/precommit.py")] = str(ROOT / "scripts/precommit.py")
                hook["entry"] = shlex.join(parts)
            (fixture / ".pre-commit-config.yaml").write_bytes(yaml.safe_dump(config).encode("utf-8"))
            (fixture / ".gitattributes").write_bytes(b"* text=auto eol=lf\n")

            def git(*arguments):
                return subprocess.check_output([tools["git"], *arguments], cwd=fixture, env=env)

            git("init", "-q")
            file = fixture / "sample.py"
            staged, unstaged = b"value = 1\n", b"value = (\n"
            file.write_bytes(staged)
            git("add", ".gitattributes", ".pre-commit-config.yaml", "sample.py")
            file.write_bytes(unstaged)
            installed = subprocess.run(
                [sys.executable, "-m", "pre_commit", "install"], cwd=fixture, env=env, capture_output=True
            )
            self.assertEqual(installed.returncode, 0, installed.stderr.decode(errors="replace"))
            result = subprocess.run(
                [tools["git"], "hook", "run", "pre-commit"], cwd=fixture, env=env, capture_output=True
            )
            self.assertEqual(result.returncode, 0, (result.stdout + result.stderr).decode(errors="replace"))
            self.assertEqual(git("show", ":sample.py"), staged)
            self.assertEqual(file.read_bytes(), unstaged)
            git("add", "sample.py")
            failed = subprocess.run(
                [tools["git"], "hook", "run", "pre-commit"], cwd=fixture, env=env, capture_output=True
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(git("show", ":sample.py"), unstaged)
            self.assertEqual(file.read_bytes(), unstaged)


if __name__ == "__main__":
    unittest.main()
