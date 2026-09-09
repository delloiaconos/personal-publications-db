import sqlite3
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path
import re

import requests
import click
from jinja2 import Environment, StrictUndefined


def database_exception(message: str) -> click.ClickException:
    """Build a consistently formatted database error for the CLI."""
    return click.ClickException(f"Database error: {message}")


@contextmanager
def database_connection(dbname: str):
    """Provide an FK-aware connection with commit, rollback, and cleanup."""
    dbcon = None
    try:
        dbcon = sqlite3.connect(dbname)
        dbcon.execute("PRAGMA foreign_keys = ON")
        yield dbcon
        dbcon.commit()
    except sqlite3.Error as e:
        if dbcon is not None:
            dbcon.rollback()
        raise database_exception(str(e)) from e
    except Exception:
        if dbcon is not None:
            dbcon.rollback()
        raise
    finally:
        if dbcon is not None:
            dbcon.close()


DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)


def normalize_doi(value: str) -> str:
    """Normalize common DOI URL/prefix forms and validate the DOI shape."""
    doi = value.strip().strip("<>")
    doi = re.sub(
        r"^(?:https?://)?(?:dx\.)?doi\.org/|^doi:\s*",
        "",
        doi,
        flags=re.IGNORECASE,
    )
    doi = doi.strip()
    if not DOI_PATTERN.fullmatch(doi):
        raise click.ClickException("DOI error: invalid DOI format.")
    return doi


def metadata_text(value):
    """Return a usable CSL text field, including list-valued fields."""
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if isinstance(value, list) and value and all(isinstance(item, str) for item in value):
        value = value[0].strip()
        return value or None
    return None


def read_doi_source(value: str) -> list[str]:
    """Return normalized DOIs from a DOI value or a text file."""
    source_path = Path(value)
    if not source_path.is_file():
        return [normalize_doi(value)]

    try:
        lines = source_path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as e:
        raise click.ClickException(f"DOI file error: {e}") from e

    dois = []
    for line_number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            dois.append(normalize_doi(line))
        except click.ClickException as e:
            raise click.ClickException(
                f"DOI file error at line {line_number}: invalid DOI format."
            ) from e

    if not dois:
        raise click.ClickException("DOI file error: the file contains no DOIs.")
    return dois


def fetch_doi_metadata(doi: str) -> tuple[str, str, list[dict]]:
    """Fetch and validate CSL metadata for a normalized DOI."""
    url = "https://doi.org/" + doi
    headers = {
        "Accept": "application/vnd.citationstyles.csl+json, application/json",
        "User-Agent": "personal-publication-db/0.1 (+https://doi.org/)",
    }
    try:
        response = requests.get(url, headers=headers, timeout=(5, 30))
    except requests.RequestException as e:
        raise click.ClickException(f"DOI error: {e}") from e

    if not 200 <= response.status_code < 300:
        raise click.ClickException(
            f"DOI error: metadata request returned HTTP {response.status_code}."
        )

    try:
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        raise click.ClickException("DOI error: invalid JSON response.") from e

    title = metadata_text(data.get("title")) if isinstance(data, dict) else None
    container = (
        metadata_text(data.get("container-title"))
        if isinstance(data, dict)
        else None
    )
    authors = data.get("author") if isinstance(data, dict) else None
    if (
        title is None
        or container is None
        or not isinstance(authors, list)
        or not all(isinstance(author, dict) for author in authors)
    ):
        raise click.ClickException("DOI error: incomplete metadata response.")

    return title, container, authors


def insert_document_from_doi(
    dbcon: sqlite3.Connection, doi: str, category: str
) -> None:
    """Fetch and insert one DOI using an existing database transaction."""
    title, container, authors = fetch_doi_metadata(doi)
    dbcur = dbcon.cursor()
    existing = dbcur.execute(
        "SELECT idDocument FROM DocumentIdentifiers "
        "WHERE IdentifierType = 'DOI' AND DocumentIdentifier = ?",
        (doi,),
    ).fetchone()
    if existing:
        click.echo(
            f"DOI error: {doi} is already present in the database."
        )
        return

    dbcur.execute(
        "INSERT INTO Documents (Title, Category, Container) VALUES (?, ?, ?)",
        (title, category, container),
    )

    idDoc = dbcur.lastrowid
    if not idDoc:
        raise database_exception("Could not retrieve the new document ID.")
    dbcur.execute(
        "INSERT INTO DocumentIdentifiers "
        "(idDocument, IdentifierType, DocumentIdentifier) "
        "VALUES (?, 'DOI', ?)",
        (idDoc, doi),
    )

    for order, author in enumerate(authors):
        firstName = author.get("given", "")
        lastName = author.get("family", "")
        if not isinstance(firstName, str):
            firstName = ""
        if not isinstance(lastName, str):
            lastName = ""
        firstName = firstName.strip()
        lastName = lastName.strip()
        if not lastName and isinstance(author.get("literal"), str):
            lastName = author["literal"].strip()

        dbcur.execute(
            "SELECT idAuthor FROM Authors "
            "WHERE FirstName = ? AND LastName = ?",
            (firstName, lastName),
        )
        idAuth = dbcur.fetchone()
        if idAuth:
            idAuth = idAuth[0]
        else:
            dbcur.execute(
                "INSERT INTO Authors (FirstName, LastName) VALUES (?, ?)",
                (firstName, lastName),
            )
            idAuth = dbcur.lastrowid

        dbcur.execute(
            "INSERT INTO DocumentAuthors "
            "(idDocument, idAuthor, AuthOrder) VALUES (?, ?, ?)",
            (idDoc, idAuth, order),
        )


def load_template(template_name: str) -> str:
    """Load a template from the current directory or packaged templates."""
    local_template = Path(template_name)
    if local_template.is_file():
        return local_template.read_text(encoding="utf-8")

    template_path = Path(template_name)
    if not template_path.is_absolute() and ".." not in template_path.parts:
        packaged_template = files("ppubdb_resources").joinpath(
            "templates", template_name
        )
        if packaged_template.is_file():
            return packaged_template.read_text(encoding="utf-8")

    raise FileNotFoundError(f"template '{template_name}' was not found")


def render_tagged_documents(
    tag: str,
    documents: list[dict],
    template_name: str = "document_by_tag.md.j2",
) -> str:
    """Render a tag-filtered document list with the selected Jinja2 template."""
    template_text = load_template(template_name)
    environment = Environment(
        autoescape=False,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    return environment.from_string(template_text).render(
        tag=tag,
        documents=documents,
    )


@click.group()
def ppdb():
    """Personal Publications Database CLI"""
    pass


@ppdb.command(name='db-init')
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=False),
    help="Database name.",

)
def dbi_init(dbname):
    """Instantiate a new database."""
    try:
        sql_script = (
            files("ppubdb_resources")
            .joinpath("db.sql")
            .read_text(encoding="utf-8")
        )
    except OSError as e:
        raise click.ClickException(f"Database schema error: {e}") from e

    with database_connection(dbname) as dbcon:
        dbcon.executescript(sql_script)

    click.echo("Database created successfully.")


@ppdb.command(name='db-prune')
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def dbi_prune(dbname):
    """Remove orphaned records and compact the database."""
    cleanup_queries = (
        (
            "AuthorIdentifiers",
            """
            DELETE FROM AuthorIdentifiers
            WHERE NOT EXISTS (
                SELECT 1 FROM Authors
                WHERE Authors.idAuthor = AuthorIdentifiers.idAuthor
            )
            """,
        ),
        (
            "DocumentIdentifiers",
            """
            DELETE FROM DocumentIdentifiers
            WHERE NOT EXISTS (
                SELECT 1 FROM Documents
                WHERE Documents.idDocument = DocumentIdentifiers.idDocument
            )
            """,
        ),
        (
            "DocumentAuthors",
            """
            DELETE FROM DocumentAuthors
            WHERE NOT EXISTS (
                SELECT 1 FROM Documents
                WHERE Documents.idDocument = DocumentAuthors.idDocument
            )
               OR NOT EXISTS (
                SELECT 1 FROM Authors
                WHERE Authors.idAuthor = DocumentAuthors.idAuthor
            )
            """,
        ),
        (
            "DocumentTags",
            """
            DELETE FROM DocumentTags
            WHERE NOT EXISTS (
                SELECT 1 FROM Documents
                WHERE Documents.idDocument = DocumentTags.idDocument
            )
            """,
        ),
        (
            "DocumentKeywords",
            """
            DELETE FROM DocumentKeywords
            WHERE NOT EXISTS (
                SELECT 1 FROM Documents
                WHERE Documents.idDocument = DocumentKeywords.idDocument
            )
            """,
        ),
    )

    with database_connection(dbname) as dbcon:
        removed_by_table = {}

        for table, query in cleanup_queries:
            removed_by_table[table] = dbcon.execute(query).rowcount

        violations = dbcon.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise database_exception(
                "Foreign-key violations remain after pruning."
            )

        # VACUUM must run outside a transaction.
        dbcon.commit()
        dbcon.execute("PRAGMA optimize")
        dbcon.execute("VACUUM")

    removed_total = sum(removed_by_table.values())
    click.echo(
        f"Database pruned successfully: {removed_total} orphaned record(s) removed."
    )

@ppdb.command(name='doc-from-doi')
@click.argument(
    'doi',
    nargs=1,
    type=click.STRING,
    metavar="DOI_OR_FILE",
)
@click.argument(
    'category',
    type=click.STRING,
    default="DOCUMENT",
)
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def doc_add_from_doi(doi: str, category: str, dbname: str):
    """Add documents using a DOI or a text file containing one DOI per line."""
    dois = read_doi_source(doi)
    category = category.strip() or "DOCUMENT"

    with database_connection(dbname) as dbcon:
        for normalized_doi in dois:
            insert_document_from_doi(dbcon, normalized_doi, category)

    if len(dois) == 1:
        click.echo("Publication added successfully.")
    else:
        click.echo(f"{len(dois)} publications added successfully.")

@ppdb.command(name='auth-collapse')
@click.argument(
    'idauthor',
    nargs=1,
    type=click.INT
)
@click.argument(
    'ids',
    nargs=-1,
    type=click.INT,
)
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def author_collapse(idauthor: int, ids: tuple[int, ...], dbname: str):
    """Merge source authors into a target without leaving orphaned records."""
    source_ids = tuple(dict.fromkeys(idb for idb in ids if idb != idauthor))
    if not source_ids:
        raise database_exception("No distinct source authors were provided.")

    with database_connection(dbname) as dbcon:
        target_exists = dbcon.execute(
            "SELECT 1 FROM Authors WHERE idAuthor = ?", (idauthor,)
        ).fetchone()
        if not target_exists:
            raise database_exception(f"Target author {idauthor} does not exist.")

        placeholders = ",".join("?" for _ in source_ids)
        existing_sources = {
            row[0]
            for row in dbcon.execute(
                f"SELECT idAuthor FROM Authors WHERE idAuthor IN ({placeholders})",
                source_ids,
            )
        }
        missing_sources = [
            idb for idb in source_ids if idb not in existing_sources
        ]
        if missing_sources:
            missing = ", ".join(str(idb) for idb in missing_sources)
            raise database_exception(f"Source author(s) do not exist: {missing}.")

        for idb in source_ids:
            # Preserve the target relationship when both authors are already
            # attached to the same document. Otherwise retain the source's
            # author order while moving the relationship to the target.
            dbcon.execute(
                """
                INSERT INTO DocumentAuthors (idDocument, idAuthor, AuthOrder)
                SELECT source.idDocument, ?, source.AuthOrder
                FROM DocumentAuthors AS source
                WHERE source.idAuthor = ?
                  AND NOT EXISTS (
                      SELECT 1
                      FROM DocumentAuthors AS target
                      WHERE target.idDocument = source.idDocument
                        AND target.idAuthor = ?
                  )
                """,
                (idauthor, idb, idauthor),
            )
            dbcon.execute(
                "DELETE FROM DocumentAuthors WHERE idAuthor = ?", (idb,)
            )
            dbcon.execute(
                "UPDATE AuthorIdentifiers SET idAuthor = ? WHERE idAuthor = ?",
                (idauthor, idb),
            )
            dbcon.execute("DELETE FROM Authors WHERE idAuthor = ?", (idb,))

    click.echo("Authors collapsed successfully.")

@ppdb.command(name='auth-list')
@click.option(
    "--sort",
    metavar="[SURNAME|FIRSTNAME|MIDDLENAME]",
    default="SURNAME",
    type=click.Choice(
        ['SURNAME', 'FIRSTNAME', 'MIDDLENAME'],
        case_sensitive=False,
    ),
    help="Sort order for the author list.",
)
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
@click.option(
    "--stats", 
    is_flag=True,
    help="Enable verbose output."
)
def authors_list( sort:str, dbname:str, stats:bool ):
    """List all the authors with their IDs."""
    with database_connection(dbname) as dbcon:
        dbcur = dbcon.cursor()
        
        sort = sort.upper()
        if sort == "SURNAME":
            dbcur.execute("SELECT idAuthor, FirstName, LastName, MiddleName FROM Authors ORDER BY LastName" )
        elif sort == "FIRSTNAME":
            dbcur.execute("SELECT idAuthor, FirstName, LastName, MiddleName FROM Authors ORDER BY FirstName" )
        elif sort == "MIDDLENAME":
            dbcur.execute("SELECT idAuthor, FirstName, LastName, MiddleName FROM Authors ORDER BY MiddleName" )
        rows = dbcur.fetchall()

        for r in rows:
            if stats:
                dbcur.execute("SELECT COUNT(*) FROM DocumentAuthors WHERE idAuthor=?", (r[0],))
                doc_count = dbcur.fetchone()[0]
                click.echo(f"[{r[0]:02d}] {r[2]}, {r[1]} ({doc_count})")
            else:
                click.echo(f"[{r[0]:02d}] {r[2]}, {r[1]}")

@ppdb.command(name='doc-list')
@click.option(
    "--category", "category",
    default=None,
    help="Filter documents by category.",
)
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def doc_list( category:str, dbname:str ):
    """List all the documents with their IDs."""
    with database_connection(dbname) as dbcon:
        dbcur = dbcon.cursor()
        
        if category:
            dbcur.execute("SELECT idDocument, Category, Title, Container FROM Documents WHERE Category = ?", (category,))
        else:
            dbcur.execute("SELECT idDocument, Category, Title, Container FROM Documents ORDER BY Category")
        rows = dbcur.fetchall()

        for r in rows:
            click.echo(f'[{r[0]:02d}] "{r[2]}", in {r[3]}')


@ppdb.command(name="doc-export-tag")
@click.argument("tag", type=click.STRING)
@click.option(
    "--template",
    "template_name",
    default="document_by_tag.md.j2",
    show_default=True,
    help="Jinja2 template name or local path.",
)
@click.option(
    "--output",
    "output_path",
    default="-",
    type=click.Path(dir_okay=False, writable=True),
    help="Rendered output path; '-' writes to standard output.",
)
@click.option(
    "--name",
    "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def doc_export_tag(
    tag: str, template_name: str, output_path: str, dbname: str
):
    """Export all documents with TAG using a Jinja2 template."""
    tag = tag.strip()
    if not tag:
        raise click.ClickException("Tag error: tag cannot be empty.")

    with database_connection(dbname) as dbcon:
        rows = dbcon.execute(
            """
            SELECT d.idDocument, d.Title, d.Category, d.Container
            FROM Documents AS d
            INNER JOIN DocumentTags AS t ON t.idDocument = d.idDocument
            WHERE t.DocumentTag = ?
            ORDER BY d.Category, d.Title, d.idDocument
            """,
            (tag,),
        ).fetchall()

        author_rows = dbcon.execute(
            """
            SELECT da.idDocument, a.idAuthor, a.FirstName, a.MiddleName,
                   a.LastName, da.AuthOrder
            FROM DocumentTags AS t
            INNER JOIN DocumentAuthors AS da
                ON da.idDocument = t.idDocument
            INNER JOIN Authors AS a ON a.idAuthor = da.idAuthor
            WHERE t.DocumentTag = ?
            ORDER BY da.idDocument, da.AuthOrder, a.idAuthor
            """,
            (tag,),
        ).fetchall()

    authors_by_document = {row[0]: [] for row in rows}
    for row in author_rows:
        authors_by_document[row[0]].append(
            {
                "id": row[1],
                "first_name": row[2],
                "middle_name": row[3],
                "last_name": row[4],
                "order": row[5],
            }
        )

    documents = [
        {
            "id": row[0],
            "title": row[1],
            "category": row[2],
            "container": row[3],
            "authors": authors_by_document[row[0]],
        }
        for row in rows
    ]
    try:
        rendered = render_tagged_documents(tag, documents, template_name)
    except OSError as e:
        raise click.ClickException(f"Template error: {e}") from e

    if output_path == "-":
        click.echo(rendered, nl=False)
        return

    try:
        with click.open_file(output_path, mode="w", encoding="utf-8") as output:
            output.write(rendered)
    except OSError as e:
        raise click.ClickException(f"Output error: {e}") from e

@ppdb.command(name='category-list')
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
@click.option(
    "--stats", 
    is_flag=True,
    help="Enable verbose output."
)
def category_list( stats:bool, dbname:str ):
    """List all the documents categories."""
    with database_connection(dbname) as dbcon:
        dbcur = dbcon.cursor()
        
        dbcur.execute(
            "SELECT Category, COUNT(*) AS Docs "
            "FROM Documents GROUP BY Category ORDER BY Category"
        )
        rows = dbcur.fetchall()

        for r in rows:
            if stats:
                click.echo(f"{r[0]} ({r[1]})")
            else:
                click.echo(f"{r[0]}")

if __name__ == "__main__":
    ppdb()
    click
