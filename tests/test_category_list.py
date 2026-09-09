import sqlite3
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

from click.testing import CliRunner

from ppubdb import ppdb


class CategoryListTests(unittest.TestCase):
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
                "INSERT INTO Documents (Title, Category, Container) "
                "VALUES (?, ?, ?)",
                [
                    ("Article one", "ARTICLE", "Journal A"),
                    ("Report", "REPORT", "Publisher"),
                    ("Article two", "ARTICLE", "Journal B"),
                ],
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def invoke_category_list(self, *options):
        return CliRunner().invoke(
            ppdb,
            ["category-list", *options, "--name", str(self.db_path)],
        )

    def test_lists_each_category_once_in_sorted_order(self):
        result = self.invoke_category_list()

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output.splitlines(), ["ARTICLE", "REPORT"])

    def test_stats_count_documents_per_category(self):
        result = self.invoke_category_list("--stats")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            result.output.splitlines(),
            ["ARTICLE (2)", "REPORT (1)"],
        )


if __name__ == "__main__":
    unittest.main()
