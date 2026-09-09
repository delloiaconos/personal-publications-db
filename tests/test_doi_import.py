import sqlite3
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from click.testing import CliRunner

from ppubdb import ppdb


class DoiImportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "publications.db"
        with sqlite3.connect(self.db_path) as dbcon:
            dbcon.executescript(
                files("ppubdb_resources")
                .joinpath("db.sql")
                .read_text(encoding="utf-8")
            )
        self.runner = CliRunner()

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def response(payload, status_code=200):
        response = Mock(status_code=status_code)
        response.json.return_value = payload
        return response

    def test_normalizes_doi_url_and_list_metadata(self):
        response = self.response(
            {
                "title": ["A publication"],
                "container-title": ["A journal"],
                "author": [{"given": " Ada ", "family": " Lovelace "}],
            }
        )
        with patch("ppubdb.requests.get", return_value=response) as request_get:
            result = self.runner.invoke(
                ppdb,
                [
                    "doc-from-doi",
                    " <https://doi.org/10.1234/ABC.1> ",
                    "ARTICLE",
                    "--name",
                    str(self.db_path),
                ],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        request_get.assert_called_once()
        self.assertEqual(request_get.call_args.args[0], "https://doi.org/10.1234/ABC.1")
        with sqlite3.connect(self.db_path) as dbcon:
            self.assertEqual(
                dbcon.execute(
                    "SELECT Title, Category, Container FROM Documents"
                ).fetchone(),
                ("A publication", "ARTICLE", "A journal"),
            )
            self.assertEqual(
                dbcon.execute("SELECT FirstName, LastName FROM Authors").fetchone(),
                ("Ada", "Lovelace"),
            )

    @patch("ppubdb.requests.get")
    def test_imports_all_dois_from_text_file(self, request_get):
        doi_file = Path(self.temp_dir.name) / "dois.txt"
        doi_file.write_text(
            "10.1234/first\n\nhttps://doi.org/10.1234/second\n",
            encoding="utf-8",
        )
        request_get.side_effect = [
            self.response(
                {
                    "title": "First publication",
                    "container-title": "First journal",
                    "author": [{"given": "Ada", "family": "Lovelace"}],
                }
            ),
            self.response(
                {
                    "title": "Second publication",
                    "container-title": "Second journal",
                    "author": [{"given": "Grace", "family": "Hopper"}],
                }
            ),
        ]

        result = self.runner.invoke(
            ppdb,
            [
                "doc-from-doi",
                str(doi_file),
                "ARTICLE",
                "--name",
                str(self.db_path),
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output, "2 publications added successfully.\n")
        self.assertEqual(
            [call.args[0] for call in request_get.call_args_list],
            [
                "https://doi.org/10.1234/first",
                "https://doi.org/10.1234/second",
            ],
        )
        with sqlite3.connect(self.db_path) as dbcon:
            self.assertEqual(
                dbcon.execute(
                    "SELECT di.DocumentIdentifier, d.Category "
                    "FROM DocumentIdentifiers AS di "
                    "INNER JOIN Documents AS d "
                    "ON d.idDocument = di.idDocument "
                    "ORDER BY d.idDocument"
                ).fetchall(),
                [
                    ("10.1234/first", "ARTICLE"),
                    ("10.1234/second", "ARTICLE"),
                ],
            )

    @patch("ppubdb.requests.get")
    def test_rejects_invalid_doi_file_before_importing_anything(self, request_get):
        doi_file = Path(self.temp_dir.name) / "invalid-dois.txt"
        doi_file.write_text(
            "10.1234/valid\n\nnot-a-doi\n",
            encoding="utf-8",
        )

        result = self.runner.invoke(
            ppdb,
            ["doc-from-doi", str(doi_file), "--name", str(self.db_path)],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("DOI file error at line 3: invalid DOI format", result.output)
        request_get.assert_not_called()
        with sqlite3.connect(self.db_path) as dbcon:
            self.assertEqual(
                dbcon.execute("SELECT COUNT(*) FROM Documents").fetchone()[0], 0
            )

    @patch("ppubdb.requests.get")
    def test_batch_import_rolls_back_if_one_doi_fails(self, request_get):
        doi_file = Path(self.temp_dir.name) / "dois.txt"
        doi_file.write_text(
            "10.1234/first\n10.1234/failing\n",
            encoding="utf-8",
        )
        request_get.side_effect = [
            self.response(
                {
                    "title": "First publication",
                    "container-title": "First journal",
                    "author": [],
                }
            ),
            requests.ConnectionError("service unavailable"),
        ]

        result = self.runner.invoke(
            ppdb,
            ["doc-from-doi", str(doi_file), "--name", str(self.db_path)],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("DOI error: service unavailable", result.output)
        with sqlite3.connect(self.db_path) as dbcon:
            self.assertEqual(
                dbcon.execute("SELECT COUNT(*) FROM Documents").fetchone()[0], 0
            )

    @patch("ppubdb.requests.get")
    def test_rejects_invalid_doi_before_network_request(self, request_get):
        result = self.runner.invoke(
            ppdb,
            ["doc-from-doi", "not-a-doi", "--name", str(self.db_path)],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error: DOI error: invalid DOI format.", result.output)
        request_get.assert_not_called()

    @patch("ppubdb.requests.get")
    def test_rejects_duplicate_doi_without_creating_document(self, request_get):
        request_get.return_value = self.response(
            {
                "title": "A publication",
                "container-title": "A journal",
                "author": [],
            }
        )
        arguments = [
            "doc-from-doi",
            "doi:10.1234/duplicate",
            "--name",
            str(self.db_path),
        ]
        first = self.runner.invoke(ppdb, arguments)
        second = self.runner.invoke(ppdb, arguments)

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertNotEqual(second.exit_code, 0)
        self.assertIn(
            "Error: DOI error: 10.1234/duplicate is already present",
            second.output,
        )
        with sqlite3.connect(self.db_path) as dbcon:
            self.assertEqual(
                dbcon.execute("SELECT COUNT(*) FROM Documents").fetchone()[0], 1
            )

    @patch("ppubdb.requests.get")
    def test_reports_http_and_metadata_errors(self, request_get):
        request_get.return_value = self.response({}, status_code=404)
        not_found = self.runner.invoke(
            ppdb,
            ["doc-from-doi", "10.1234/missing", "--name", str(self.db_path)],
        )
        self.assertIn("Error: DOI error: metadata request returned HTTP 404", not_found.output)

        request_get.return_value = self.response({"title": "Only a title"})
        incomplete = self.runner.invoke(
            ppdb,
            ["doc-from-doi", "10.1234/incomplete", "--name", str(self.db_path)],
        )
        self.assertIn("Error: DOI error: incomplete metadata response.", incomplete.output)


if __name__ == "__main__":
    unittest.main()
