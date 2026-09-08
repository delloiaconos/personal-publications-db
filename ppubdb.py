import sqlite3
import requests
import click


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
    """Instanciate a new database."""
    dbcon = sqlite3.connect(dbname)
    dbcur = dbcon.cursor()
    with open( 'db.sql', 'r') as f:
        sql_script = f.read()
        try:
            for statement in sql_script.split(';'):
                if not statement.strip() or statement.startswith('--'):
                    continue
                dbcur.execute(statement)
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
            if dbcon.commit():
                print("Database created successfully.") 
            dbcon.close()


@ppdb.command(name='db-prune')
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def dbi_prune(dbname):
    """Prune the database."""
    pass

@ppdb.command(name='doc-from-doi')
@click.argument(
    'doi', 
    nargs=1,
    type=click.STRING,
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
def doc_add_from_doi( doi:str, category:str, dbname:str):
    """Add a document using its DOI."""
    url = "http://dx.doi.org/" + doi
    headers = { 'Accept': 'application/json' }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")
        return None

    data = response.json()
    if not all(key in data for key in ('title', 'author', 'container-title')):
        print("Invalid data format received.")
        return None

    dbcon = sqlite3.connect(dbname)
    dbcur = dbcon.cursor()
    dbcur.execute("INSERT INTO Documents (Title, Category, Container) VALUES (?, ?, ?)", (data['title'], category, data['container-title']))
    
    idDoc = dbcur.lastrowid
    if not idDoc:
        print("Failed to retrieve document ID.")
        return None 
    dbcur.execute("INSERT INTO DocumentIdentifiers (idDocument, IdentifierType, DocumentIdentifier) VALUES (?, 'DOI', ?)", (idDoc, doi))
    
    for order, author in enumerate( data['author'] ):
        firstName = author.get('given', '')
        lastName = author.get('family', '')

        dbcur.execute("SELECT idAuthor FROM Authors WHERE FirstName = ? AND LastName = ?", (firstName, lastName))
        idAuth = dbcur.fetchone()
        if idAuth:
            idAuth = idAuth[0]
        else:
            dbcur.execute("INSERT INTO Authors (FirstName, LastName) VALUES (?, ?)", (firstName, lastName))
            idAuth = dbcur.lastrowid
        
        dbcur.execute("INSERT INTO DocumentAuthors (idDocument, idAuthor, AuthOrder) VALUES (?, ?, ?)", (idDoc, idAuth, order))
    dbcon.commit()
    print("Publication added successfully.")

    dbcon.close()

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
        raise click.ClickException("No distinct source authors were provided.")

    dbcon = sqlite3.connect(dbname)
    try:
        dbcon.execute("PRAGMA foreign_keys = ON")

        with dbcon:
            target_exists = dbcon.execute(
                "SELECT 1 FROM Authors WHERE idAuthor = ?", (idauthor,)
            ).fetchone()
            if not target_exists:
                raise click.ClickException(
                    f"Target author {idauthor} does not exist."
                )

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
                raise click.ClickException(
                    f"Source author(s) do not exist: {missing}."
                )

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
    except sqlite3.Error as e:
        raise click.ClickException(f"Database error: {e}") from e
    finally:
        dbcon.close()

@ppdb.command(name='auth-list')
@click.option(
    "--sort", "[SURNAME|FIRSTNAME]",
    default="SURNAME",
    type=click.Choice(['SURNAME', 'FIRSTNAME', "MIDDLENAME"], case_sensitive=False),
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
    try:
        dbcon = sqlite3.connect(dbname)
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
                print( f"""[{r[0]:02d}] {r[2]}, {r[1]} ({doc_count})""" )
            else:
                print( f"""[{r[0]:02d}] {r[2]}, {r[1]}""" )

        dbcon.close()
    except sqlite3.OperationalError as e:
        print(e)

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
    try:
        dbcon = sqlite3.connect(dbname)
        dbcur = dbcon.cursor()
        
        if category:
            dbcur.execute("SELECT idDocument, Category, Title, Container FROM Documents WHERE Category = ?", (category,))
        else:
            dbcur.execute("SELECT idDocument, Category, Title, Container FROM Documents ORDER BY Category")
        rows = dbcur.fetchall()

        for r in rows:
            print( f"""[{r[0]:02d}] "{r[2]}", in {r[3]}""" )    

        dbcon.close()
    except sqlite3.OperationalError as e:
        print(e)

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
    try:
        dbcon = sqlite3.connect(dbname)
        dbcur = dbcon.cursor()
        
        dbcur.execute("SELECT DISTINCT Category, COUNT(*) as Docs FROM Documents ORDER BY Category")
        rows = dbcur.fetchall()

        for r in rows:
            if stats:
                print( f"""{r[0]} ({r[1]})""" )
            else:
                print( f"""{r[0]}""" )

        dbcon.close()
    except sqlite3.OperationalError as e:
        print(e)

if __name__ == "__main__":
    ppdb()
    click
