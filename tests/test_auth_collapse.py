import sqlite3
import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from ppubdb import ppdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AuthorCollapseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "publications.db"
        with sqlite3.connect(self.db_path) as dbcon:
            dbcon.executescript((PROJECT_ROOT / "db.sql").read_text())
            dbcon.executemany(
                "INSERT INTO Authors (idAuthor, FirstName, LastName) VALUES (?, ?, ?)",
                [
                    (1, "Preferred", "Author"),
                    (2, "Duplicate", "Author"),
                ],
            )
            dbcon.executemany(
                "INSERT INTO Documents (idDocument, Title, Category, Container) VALUES (?, ?, ?, ?)",
                [
                    (1, "Shared paper", "ARTICLE", "Journal"),
                    (2, "Source-only paper", "ARTICLE", "Journal"),
                ],
            )
            dbcon.executemany(
                "INSERT INTO DocumentAuthors (idDocument, idAuthor, AuthOrder) VALUES (?, ?, ?)",
                [
                    (1, 1, 0),
                    (1, 2, 1),
                    (2, 2, 3),
                ],
            )
            dbcon.execute(
                "INSERT INTO AuthorIdentifiers "
                "(idAuthor, IdentifierType, AuthorIdentifier) VALUES (?, ?, ?)",
                (2, "ORCID", "0000-0000-0000-0002"),
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def invoke_collapse(self, *author_ids):
        return CliRunner().invoke(
            ppdb,
            [
                "auth-collapse",
                *(str(author_id) for author_id in author_ids),
                "--name",
                str(self.db_path),
            ],
        )

    def test_collapse_moves_relationships_and_identifiers_without_orphans(self):
        result = self.invoke_collapse(1, 2)

        self.assertEqual(result.exit_code, 0, result.output)
        with sqlite3.connect(self.db_path) as dbcon:
            self.assertEqual(
                dbcon.execute(
                    "SELECT idAuthor FROM Authors ORDER BY idAuthor"
                ).fetchall(),
                [(1,)],
            )
            self.assertEqual(
                dbcon.execute(
                    "SELECT idDocument, idAuthor, AuthOrder "
                    "FROM DocumentAuthors ORDER BY idDocument"
                ).fetchall(),
                [(1, 1, 0), (2, 1, 3)],
            )
            self.assertEqual(
                dbcon.execute(
                    "SELECT idAuthor, AuthorIdentifier FROM AuthorIdentifiers"
                ).fetchall(),
                [(1, "0000-0000-0000-0002")],
            )
            self.assertEqual(dbcon.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_target_id_in_sources_is_not_deleted(self):
        result = self.invoke_collapse(1, 1, 2)

        self.assertEqual(result.exit_code, 0, result.output)
        with sqlite3.connect(self.db_path) as dbcon:
            self.assertEqual(
                dbcon.execute(
                    "SELECT idAuthor FROM Authors ORDER BY idAuthor"
                ).fetchall(),
                [(1,)],
            )
            self.assertEqual(dbcon.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_missing_source_rolls_back_without_changes(self):
        result = self.invoke_collapse(1, 2, 999)

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Source author(s) do not exist: 999", result.output)
        with sqlite3.connect(self.db_path) as dbcon:
            self.assertEqual(
                dbcon.execute(
                    "SELECT idAuthor FROM Authors ORDER BY idAuthor"
                ).fetchall(),
                [(1,), (2,)],
            )
            self.assertEqual(
                dbcon.execute(
                    "SELECT COUNT(*) FROM DocumentAuthors WHERE idAuthor = 2"
                ).fetchone()[0],
                2,
            )


if __name__ == "__main__":
    unittest.main()
