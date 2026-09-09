import sqlite3
import unittest
from pathlib import Path

from click.testing import CliRunner

from ppubdb import ppdb


class DatabaseInitTests(unittest.TestCase):
    def test_initializes_database_outside_project_directory(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(ppdb, ["db-init", "--db", "publications.db"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Database created successfully.", result.output)
            self.assertTrue(Path("publications.db").is_file())

            with sqlite3.connect("publications.db") as dbcon:
                tables = {
                    row[0]
                    for row in dbcon.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }

        self.assertTrue(
            {
                "Authors",
                "AuthorIdentifiers",
                "Documents",
                "DocumentIdentifiers",
                "DocumentAuthors",
                "DocumentTags",
                "DocumentKeywords",
            }.issubset(tables)
        )


if __name__ == "__main__":
    unittest.main()
