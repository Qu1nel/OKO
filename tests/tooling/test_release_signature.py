"""Check real tag signatures with a disposable key and an existing commit."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.release import validate_tag

ROOT = Path(__file__).resolve().parents[2]


class TagSignatureTests(unittest.TestCase):
    def test_signed_unsigned_tampered_and_unknown_key(self):
        (ROOT / ".work").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".work", prefix="tag-signature-") as temporary:
            gpg = shutil.which("gpg")
            if gpg is None:
                raise RuntimeError("GnuPG is required for release signature tests")
            base = Path(temporary)
            repository = base / "repository"
            keyring = base / "gnupg"
            keyring.mkdir(mode=0o700)
            subprocess.run(
                [
                    "git",
                    "-c",
                    f"safe.directory={ROOT.as_posix()}",
                    "clone",
                    "--quiet",
                    "--no-checkout",
                    "--no-hardlinks",
                    str(ROOT),
                    str(repository),
                ],
                check=True,
                capture_output=True,
            )
            with patch.dict(os.environ, {"GNUPGHOME": str(keyring), "GIT_CONFIG_COUNT": "0"}):

                def git(*arguments, data=None):
                    result = subprocess.run(
                        ["git", *arguments],
                        cwd=repository,
                        input=data,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                    return result.stdout

                try:
                    subprocess.run(
                        [
                            gpg,
                            "--batch",
                            "--pinentry-mode",
                            "loopback",
                            "--passphrase",
                            "",
                            "--quick-generate-key",
                            "OKO fixture <release@example.invalid>",
                            "ed25519",
                            "sign",
                            "1d",
                        ],
                        check=True,
                        capture_output=True,
                    )
                    for name, value in {
                        "user.name": "OKO fixture",
                        "user.email": "release@example.invalid",
                        "user.signingkey": "release@example.invalid",
                        "gpg.format": "openpgp",
                        "gpg.program": str(Path(gpg).resolve()),
                        "tag.gpgsign": "false",
                    }.items():
                        git("config", name, value)
                    git("tag", "-a", "v0.1.1", "-m", "Unsigned fixture")
                    with self.assertRaisesRegex(ValueError, "signature"):
                        validate_tag(repository, "v0.1.1")

                    git("tag", "-s", "v0.1.0", "-m", "Release fixture")
                    validate_tag(repository, "v0.1.0")
                    payload = git("cat-file", "tag", "v0.1.0").replace(b"Release fixture", b"Tampered fixture")
                    changed = git("hash-object", "-w", "-t", "tag", "--stdin", data=payload).decode().strip()
                    git("update-ref", "refs/tags/tampered", changed)
                    with self.assertRaisesRegex(ValueError, "signature"):
                        validate_tag(repository, "tampered")

                    unknown = base / "unknown-keys"
                    unknown.mkdir(mode=0o700)
                    with patch.dict(os.environ, {"GNUPGHOME": str(unknown)}):
                        with self.assertRaisesRegex(ValueError, "signature"):
                            validate_tag(repository, "v0.1.0")
                        public_key = subprocess.check_output(
                            [gpg, "--armor", "--export", "release@example.invalid"],
                            env={**os.environ, "GNUPGHOME": str(keyring)},
                        )
                        subprocess.run([gpg, "--batch", "--import"], input=public_key, capture_output=True, check=True)
                        validate_tag(repository, "v0.1.0")
                finally:
                    subprocess.run(["gpgconf", "--kill", "gpg-agent"], check=False, capture_output=True)


if __name__ == "__main__":
    unittest.main()
