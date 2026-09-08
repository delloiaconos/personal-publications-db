import sqlite3
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

from click.testing import CliRunner

from ppubdb import ppdb


class DatabasePruneTests(unittest.TestCase):
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
                "INSERT INTO Authors (idAuthor, FirstName, LastName) VALUES (?, ?, ?)",
                [
                    (1, "Linked", "Author"),
                    (2, "Unlinked", "Author"),
                ],
            )
            dbcon.execute(
                "INSERT INTO Documents "
                "(idDocument, Title, Category, Container) VALUES (?, ?, ?, ?)",
                (1, "Valid paper", "ARTICLE", "Journal"),
            )
            dbcon.execute(
                "INSERT INTO DocumentAuthors "
                "(idDocument, idAuthor, AuthOrder) VALUES (?, ?, ?)",
                (1, 1, 0),
            )
            dbcon.execute(
                "INSERT INTO DocumentTags (idDocument, DocumentTag) VALUES (?, ?)",
                (1, "valid"),
            )

            # Foreign-key enforcement is intentionally off here to simulate a
            # legacy database containing records orphaned by older commands.
            dbcon.execute(
                "INSERT INTO AuthorIdentifiers "
                "(idAuthor, IdentifierType, AuthorIdentifier) VALUES (?, ?, ?)",
                (99, "ORCID", "orphan-author-id"),
            )
            dbcon.execute(
                "INSERT INTO DocumentIdentifiers "
                "(idDocument, IdentifierType, DocumentIdentifier) VALUES (?, ?, ?)",
                (99, "DOI", "orphan-document-id"),
            )
            dbcon.execute(
                "INSERT INTO DocumentAuthors "
                "(idDocument, idAuthor, AuthOrder) VALUES (?, ?, ?)",
                (99, 99, 0),
            )
            dbcon.execute(
                "INSERT INTO DocumentTags (idDocument, DocumentTag) VALUES (?, ?)",
                (99, "orphan"),
            )
            dbcon.execute(
                "INSERT INTO DocumentKeywords (idDocument, Keyword) VALUES (?, ?)",
                (99, "orphan"),
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_removes_only_orphaned_records(self):
        result = CliRunner().invoke(
            ppdb,
            ["db-prune", "--name", str(self.db_path)],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("5 orphaned record(s) removed", result.output)

        with sqlite3.connect(self.db_path) as dbcon:
            self.assertEqual(dbcon.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(
                dbcon.execute(
                    "SELECT idAuthor FROM Authors ORDER BY idAuthor"
                ).fetchall(),
                [(1,), (2,)],
            )
            self.assertEqual(
                dbcon.execute(
                    "SELECT idDocument, idAuthor FROM DocumentAuthors"
                ).fetchall(),
                [(1, 1)],
            )
            self.assertEqual(
                dbcon.execute(
                    "SELECT idDocument, DocumentTag FROM DocumentTags"
                ).fetchall(),
                [(1, "valid")],
            )

    def test_reports_zero_when_database_is_already_clean(self):
        with sqlite3.connect(self.db_path) as dbcon:
            dbcon.execute("DELETE FROM AuthorIdentifiers WHERE idAuthor = 99")
            dbcon.execute("DELETE FROM DocumentIdentifiers WHERE idDocument = 99")
            dbcon.execute("DELETE FROM DocumentAuthors WHERE idDocument = 99")
            dbcon.execute("DELETE FROM DocumentTags WHERE idDocument = 99")
            dbcon.execute("DELETE FROM DocumentKeywords WHERE idDocument = 99")

        result = CliRunner().invoke(
            ppdb,
            ["db-prune", "--name", str(self.db_path)],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("0 orphaned record(s) removed", result.output)


if __name__ == "__main__":
    unittest.main()
