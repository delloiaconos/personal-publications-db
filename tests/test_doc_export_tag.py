import sqlite3
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

from click.testing import CliRunner

from ppubdb import ppdb


class DocumentTagExportTests(unittest.TestCase):
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
                "INSERT INTO Documents "
                "(idDocument, Title, Category, Container) VALUES (?, ?, ?, ?)",
                [
                    (1, "Tagged article", "ARTICLE", "Journal A"),
                    (2, "Other document", "REPORT", "Report B"),
                    (3, "Second tagged article", "ARTICLE", "Journal C"),
                ],
            )
            dbcon.executemany(
                "INSERT INTO DocumentTags (idDocument, DocumentTag) VALUES (?, ?)",
                [(1, "important"), (2, "other"), (3, "important")],
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_exports_only_documents_with_requested_tag(self):
        output_path = Path(self.temp_dir.name) / "important.md"
        result = CliRunner().invoke(
            ppdb,
            [
                "doc-export-tag",
                "important",
                "--name",
                str(self.db_path),
                "--output",
                str(output_path),
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output, "")
        content = output_path.read_text(encoding="utf-8")
        self.assertIn("# Documents tagged `important`", content)
        self.assertIn("Tagged article", content)
        self.assertIn("Second tagged article", content)
        self.assertNotIn("Other document", content)
        self.assertLess(
            content.index("Second tagged article"),
            content.index("Tagged article"),
        )

    def test_writes_markdown_to_stdout_and_handles_no_matches(self):
        result = CliRunner().invoke(
            ppdb,
            ["doc-export-tag", "missing", "--name", str(self.db_path)],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("# Documents tagged `missing`", result.output)
        self.assertIn("No documents found with this tag.", result.output)

    def test_rejects_empty_tag(self):
        result = CliRunner().invoke(
            ppdb,
            ["doc-export-tag", "   ", "--name", str(self.db_path)],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error: Tag error: tag cannot be empty.", result.output)


if __name__ == "__main__":
    unittest.main()
