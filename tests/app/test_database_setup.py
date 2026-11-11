import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class DatabaseSetupTests(SimpleTestCase):
    def test_migrate_creates_a_new_sqlite_directory_and_reuses_the_file(self) -> None:
        work = settings.BASE_DIR / ".work"
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as temporary:
            path = Path(temporary) / "new profile" / "data" / "oko.sqlite3"
            command = [sys.executable, "manage.py", "migrate", "--noinput"]
            environment = {**os.environ, "OKO_DB_PATH": str(path)}
            self.assertFalse(path.parent.exists())
            first = subprocess.run(command, cwd=settings.BASE_DIR, env=environment, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue(path.is_file())
            with closing(sqlite3.connect(path)) as database:
                database.execute(
                    "INSERT INTO oko_card (title, question, answer, created_at) VALUES ('', 'Q', 'A', CURRENT_TIMESTAMP)"
                )
                database.commit()

            second = subprocess.run(command, cwd=settings.BASE_DIR, env=environment, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            with closing(sqlite3.connect(path)) as database:
                self.assertEqual(database.execute("SELECT question, answer FROM oko_card").fetchall(), [("Q", "A")])
