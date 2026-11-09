"""Test archive extraction safety and release consistency with isolated fixtures."""

import io
import json
import os
import tempfile
import unittest
import urllib.error
import zipfile
from email.message import Message
from pathlib import Path
from unittest.mock import patch

from scripts.publish_release import api, publish
from scripts.release import release_notes
from scripts.setup_node import bootstrap_lock, check_digest, extract

WORK = Path(__file__).resolve().parents[1] / ".work"


def setUpModule():
    WORK.mkdir(exist_ok=True)


class ArchiveTests(unittest.TestCase):
    def test_only_one_bootstrap_can_hold_the_installation_lock(self):
        with tempfile.TemporaryDirectory(dir=WORK) as temporary:
            tools = Path(temporary)
            with bootstrap_lock(tools):
                with self.assertRaisesRegex(RuntimeError, "already running"):
                    with bootstrap_lock(tools):
                        self.fail("A second bootstrap acquired the same lock")
            with self.assertRaisesRegex(ValueError, "interrupted"):
                with bootstrap_lock(tools):
                    raise ValueError("interrupted")
            self.assertFalse((tools / ".setup-node.lock").exists())

    def test_corrupt_download_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "checksum"):
            check_digest(b"wrong archive", "sha256", "00" * 32)

    def test_zip_traversal_is_rejected_before_extraction(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("../escaped.txt", "bad")
        with tempfile.TemporaryDirectory(dir=WORK) as temporary:
            target = Path(temporary) / "extract"
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                extract(data.getvalue(), target, zipped=True)
            self.assertFalse((Path(temporary) / "escaped.txt").exists())


class ReleaseTests(unittest.TestCase):
    @patch("builtins.print")
    def test_existing_release_is_verified_and_never_overwritten(self, _print):
        commit = "a" * 40
        expected = {"tag_name": "v0.1.0", "target_commitish": commit, "body": "- First", "draft": False}
        ref = {"object": {"type": "tag", "sha": "b" * 40}}
        tagged = {"object": {"type": "commit", "sha": commit}, "verification": {"verified": True, "reason": "valid"}}
        with patch("scripts.publish_release.api", side_effect=[ref, tagged, expected]) as request:
            publish("owner/oko", "v0.1.0", commit, "- First\n")
            self.assertTrue(all(call.args[0] == "GET" for call in request.call_args_list))
        for changed in [{**expected, "body": "different"}, {**expected, "target_commitish": "c" * 40}]:
            with patch("scripts.publish_release.api", side_effect=[ref, tagged, changed]) as request:
                with self.assertRaisesRegex(ValueError, "differs|differ"):
                    publish("owner/oko", "v0.1.0", commit, "- First\n")
                self.assertTrue(all(call.args[0] == "GET" for call in request.call_args_list))
        with patch("scripts.publish_release.api", side_effect=[ref, tagged, None, expected]) as request:
            publish("owner/oko", "v0.1.0", commit, "- First\n")
            self.assertEqual(request.call_args_list[-1].args[2]["target_commitish"], commit)

    def test_unverified_tag_never_reaches_release_creation(self):
        ref = {"object": {"type": "tag", "sha": "b" * 40}}
        for verification in [
            None,
            {},
            {"verified": False, "reason": "unsigned"},
            {"verified": False, "reason": "invalid"},
            {"verified": False, "reason": "gpgverify_unavailable"},
        ]:
            with self.subTest(verification=verification):
                tagged = {"object": {"type": "commit", "sha": "a" * 40}, "verification": verification}
                with patch("scripts.publish_release.api", side_effect=[ref, tagged]) as request:
                    with self.assertRaisesRegex(ValueError, "signature"):
                        publish("owner/oko", "v0.1.0", "a" * 40, "- First\n")
                    self.assertEqual(request.call_count, 2)

    def test_only_explicit_404_means_absent(self):
        with patch.dict(os.environ, {"GH_TOKEN": "fixture"}):
            for code in [401, 403, 500]:
                error = urllib.error.HTTPError("https://example.invalid", code, "fixture", Message(), io.BytesIO())
                with patch("urllib.request.urlopen", side_effect=error):
                    with self.assertRaises(urllib.error.HTTPError):
                        api("GET", "fixture", allow_missing=True)
            error = urllib.error.HTTPError("https://example.invalid", 404, "fixture", Message(), io.BytesIO())
            with patch("urllib.request.urlopen", side_effect=error):
                self.assertIsNone(api("GET", "fixture", allow_missing=True))
                with self.assertRaises(urllib.error.HTTPError):
                    api("GET", "fixture")
            with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
                with self.assertRaises(urllib.error.URLError):
                    api("GET", "fixture", allow_missing=True)

    def test_notes_and_mismatched_versions(self):
        with tempfile.TemporaryDirectory(dir=WORK) as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text('[project]\nname="oko"\nversion="0.1.0"\n')
            (root / "uv.lock").write_text('[[package]]\nname="oko"\nversion="0.1.0"\n')
            (root / "package.json").write_text(json.dumps({"version": "0.1.0"}))
            (root / "package-lock.json").write_text(
                json.dumps({"version": "0.1.0", "packages": {"": {"version": "0.1.0"}}})
            )
            (root / "CHANGELOG.md").write_text("## [Unreleased]\n\n- Later\n")
            with self.assertRaisesRegex(ValueError, "Missing dated"):
                release_notes(root, "v0.1.0")
            (root / "CHANGELOG.md").write_text("## [0.1.0] - 2026-01-01\n\n- First release\n")
            self.assertEqual(release_notes(root, "v0.1.0"), "- First release\n")
            with self.assertRaisesRegex(ValueError, "Expected tag"):
                release_notes(root, "v0.2.0")
            (root / "package.json").write_text(json.dumps({"version": "0.2.0"}))
            with self.assertRaisesRegex(ValueError, "disagree"):
                release_notes(root, "v0.1.0")


if __name__ == "__main__":
    unittest.main()
