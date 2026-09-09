import sqlite3
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

from click.testing import CliRunner

from ppubdb import ppdb, render_tagged_documents


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
                [
                    (1, "important"),
                    (1, "featured"),
                    (2, "other"),
                    (3, "important"),
                ],
            )
            dbcon.executemany(
                "INSERT INTO Authors "
                "(idAuthor, FirstName, MiddleName, LastName) VALUES (?, ?, ?, ?)",
                [
                    (1, "Second", None, "Author"),
                    (2, "First", "Middle", "Author"),
                    (3, "Third", None, "Writer"),
                ],
            )
            dbcon.executemany(
                "INSERT INTO DocumentAuthors "
                "(idDocument, idAuthor, AuthOrder) VALUES (?, ?, ?)",
                [(1, 1, 1), (1, 2, 0), (1, 3, 2)],
            )
            dbcon.execute(
                "INSERT INTO DocumentIdentifiers "
                "(idDocument, IdentifierType, DocumentIdentifier) "
                "VALUES (?, ?, ?)",
                (1, "DOI", "10.1234/tagged"),
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
                "--db",
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
            ["doc-export-tag", "missing", "--db", str(self.db_path)],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("# Documents tagged `missing`", result.output)
        self.assertIn("No documents found with this tag.", result.output)

    def test_omitting_tag_exports_every_document_once(self):
        result = CliRunner().invoke(
            ppdb,
            ["doc-export-tag", "--db", str(self.db_path)],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("# All documents", result.output)
        self.assertIn("Tagged article", result.output)
        self.assertIn("Other document", result.output)
        self.assertIn("Second tagged article", result.output)
        self.assertEqual(result.output.count("- **"), 3)

    def test_custom_template_receives_authors_in_publication_order(self):
        template_path = Path(self.temp_dir.name) / "citation.txt.j2"
        template_path.write_text(
            "{% for document in documents %}"
            "{{ document.title }}: "
            "{% for author in document.authors %}"
            "{{ author.first_name }} {{ author.middle_name or '' }} "
            "{{ author.last_name }}{% if not loop.last %}, {% endif %}"
            "{% endfor %}\n"
            "{% endfor %}",
            encoding="utf-8",
        )

        result = CliRunner().invoke(
            ppdb,
            [
                "doc-export-tag",
                "important",
                "--template",
                str(template_path),
                "--db",
                str(self.db_path),
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(
            "Tagged article: First Middle Author, Second  Author",
            result.output,
        )

    def test_bundled_ieee_template_formats_citation(self):
        result = CliRunner().invoke(
            ppdb,
            [
                "doc-export-tag",
                "important",
                "--template",
                "ieee.txt.j2",
                "--db",
                str(self.db_path),
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(
            "F. M. Author, S. Author, and T. Writer, “Tagged article,” "
            "Journal A, doi: 10.1234/tagged.",
            result.output,
        )

    def test_ieee_template_supports_complete_citation_fields(self):
        rendered = render_tagged_documents(
            "example",
            [
                {
                    "title": "Reassessing the proper place of man and machine "
                    "in translation: A pre-translation scenario",
                    "container": "Mach. Transl.",
                    "doi": "10.1007/s10590-018-9223-9",
                    "authors": [
                        {
                            "first_name": "Jonathan",
                            "middle_name": None,
                            "last_name": "Ive",
                        },
                        {
                            "first_name": "Alice",
                            "middle_name": None,
                            "last_name": "Max",
                        },
                        {
                            "first_name": "François",
                            "middle_name": None,
                            "last_name": "Yvon",
                        },
                    ],
                    "volume": "32",
                    "issue": "4",
                    "pages": "279–308",
                    "month": "Dec.",
                    "year": "2018",
                }
            ],
            "ieee.txt.j2",
        )

        self.assertEqual(
            rendered,
            "J. Ive, A. Max, and F. Yvon, “Reassessing the proper place of "
            "man and machine in translation: A pre-translation scenario,” "
            "Mach. Transl., vol. 32, no. 4, pp. 279–308, Dec. 2018, doi: "
            "10.1007/s10590-018-9223-9.\n",
        )

    def test_local_template_takes_precedence_over_packaged_template(self):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.temp_dir.name):
            Path("document_by_tag.md.j2").write_text(
                "Local template: {{ tag }}\n", encoding="utf-8"
            )
            result = runner.invoke(
                ppdb,
                ["doc-export-tag", "important", "--db", str(self.db_path)],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output, "Local template: important\n")

    def test_reports_missing_template(self):
        result = CliRunner().invoke(
            ppdb,
            [
                "doc-export-tag",
                "important",
                "--template",
                "missing-template.j2",
                "--db",
                str(self.db_path),
            ],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            "Template error: template 'missing-template.j2' was not found",
            result.output,
        )

    def test_rejects_empty_tag(self):
        result = CliRunner().invoke(
            ppdb,
            ["doc-export-tag", "   ", "--db", str(self.db_path)],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error: Tag error: tag cannot be empty.", result.output)


if __name__ == "__main__":
    unittest.main()
