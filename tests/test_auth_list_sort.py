import sqlite3
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

from click.testing import CliRunner

from ppubdb import ppdb


class AuthorListSortTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "publications.db"
        with sqlite3.connect(self.db_path) as dbcon:
            dbcon.executescript(
                files("ppubdb_resources")
                .joinpath("db.sql")
                .read_text(encoding="utf-8")
            )
            dbcon.executemany(
                "INSERT INTO Authors (FirstName, LastName, MiddleName) VALUES (?, ?, ?)",
                [
                    ("Ada", "Lovelace", "Byron"),
                    ("Alan", "Turing", "Mathison"),
                ],
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_help_shows_complete_metavar(self):
        result = CliRunner().invoke(ppdb, ["auth-list", "--help"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("--sort [SURNAME|FIRSTNAME|MIDDLENAME]", result.output)
        self.assertNotIn("[SURNAME|FIRSTNAME], --sort", result.output)

    def test_all_sort_values_are_accepted(self):
        runner = CliRunner()
        for value in ("SURNAME", "FIRSTNAME", "MIDDLENAME"):
            with self.subTest(value=value):
                result = runner.invoke(
                    ppdb,
                    ["auth-list", "--sort", value, "--db", str(self.db_path)],
                )
                self.assertEqual(result.exit_code, 0, result.output)


if __name__ == "__main__":
    unittest.main()
