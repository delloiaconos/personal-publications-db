import sqlite3
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from click.testing import CliRunner

from ppubdb import ppdb


class DatabaseErrorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "empty.db"
        self.db_path.touch()
        self.runner = CliRunner()

    def tearDown(self):
        self.temp_dir.cleanup()

    def assert_database_error(self, result):
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error: Database error:", result.output)

    def test_all_database_commands_report_sqlite_errors_consistently(self):
        commands = (
            ["auth-list"],
            ["doc-list"],
            ["category-list"],
            ["doc-export-tag", "important"],
            ["db-prune"],
            ["auth-collapse", "1", "2"],
        )

        for command in commands:
            with self.subTest(command=command[0]):
                result = self.runner.invoke(
                    ppdb,
                    [*command, "--db", str(self.db_path)],
                )
                self.assert_database_error(result)

    def test_db_init_reports_connection_error_consistently(self):
        invalid_path = self.temp_dir.name + "/missing/publications.db"

        result = self.runner.invoke(
            ppdb,
            ["db-init", "--db", invalid_path],
        )

        self.assert_database_error(result)

    @patch("ppubdb.requests.get")
    def test_doi_import_reports_database_error_consistently(self, request_get):
        response = Mock(status_code=200)
        response.json.return_value = {
            "title": "Publication",
            "container-title": "Journal",
            "author": [{"given": "Ada", "family": "Lovelace"}],
        }
        request_get.return_value = response

        result = self.runner.invoke(
            ppdb,
            ["doc-from-doi", "10.0000/example", "--db", str(self.db_path)],
        )

        self.assert_database_error(result)

    @patch("ppubdb.requests.get")
    def test_doi_network_error_has_nonzero_exit_code(self, request_get):
        request_get.side_effect = requests.ConnectionError("service unavailable")

        result = self.runner.invoke(
            ppdb,
            ["doc-from-doi", "10.0000/example", "--db", str(self.db_path)],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error: DOI error: service unavailable", result.output)

    @patch("ppubdb.requests.get")
    def test_doi_database_error_rolls_back_partial_import(self, request_get):
        with sqlite3.connect(self.db_path) as dbcon:
            dbcon.executescript(
                files("ppubdb_resources")
                .joinpath("db.sql")
                .read_text(encoding="utf-8")
            )

        response = Mock(status_code=200)
        response.json.return_value = {
            "title": "Publication",
            "container-title": "Journal",
            # Repeating the same author violates the DocumentAuthors primary key
            # after the document and first relationship have been inserted.
            "author": [
                {"given": "Ada", "family": "Lovelace"},
                {"given": "Ada", "family": "Lovelace"},
            ],
        }
        request_get.return_value = response

        result = self.runner.invoke(
            ppdb,
            ["doc-from-doi", "10.0000/example", "--db", str(self.db_path)],
        )

        self.assert_database_error(result)
        with sqlite3.connect(self.db_path) as dbcon:
            self.assertEqual(
                dbcon.execute("SELECT COUNT(*) FROM Documents").fetchone()[0], 0
            )
            self.assertEqual(
                dbcon.execute("SELECT COUNT(*) FROM Authors").fetchone()[0], 0
            )
