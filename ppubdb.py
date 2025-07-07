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
)
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def author_collapse( idauthor:int, ids:list, dbname:str):
    """Collapse multiple authors to a single one, it only replaces the author in documents and deletes the collapsed."""
    try:
        dbcon = sqlite3.connect(dbname)
        dbcur = dbcon.cursor()

        for idb in ids:
            dbcur.execute("UPDATE OR IGNORE DocumentAuthors SET idAuthor=? WHERE idAuthor=?", (idauthor, idb))
        dbcon.commit()

        for idb in ids:
            dbcur.execute("DELETE FROM Authors WHERE idAuthor=?", (idb,) )
        dbcon.commit()

        print("Authors collapsed succesfully.")
        dbcon.close()
    except sqlite3.OperationalError as e:
        print(e)

@ppdb.command(name='auth-list')
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def authors_list( dbname:str):
    """List all the authors with their IDs."""
    try:
        dbcon = sqlite3.connect(dbname)
        dbcur = dbcon.cursor()
        
        dbcur.execute("SELECT idAuthor, FirstName, LastName, MiddleName FROM Authors" )
        rows = dbcur.fetchall()

        for r in rows:
            print( f"""[{r[0]:02d}] {r[2]}, {r[1]}""" )    

        dbcon.close()
    except sqlite3.OperationalError as e:
        print(e)

@ppdb.command(name='doc-list')
@click.option(
    "--name", "dbname",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def doc_list( dbname:str):
    """List all the authors with their IDs."""
    try:
        dbcon = sqlite3.connect(dbname)
        dbcur = dbcon.cursor()
        
        dbcur.execute("SELECT idDocument, Category, Title, Container FROM Documents ORDER BY Category" )
        rows = dbcur.fetchall()

        for r in rows:
            print( f"""[{r[0]:02d}] "{r[2]}", in {r[3]}""" )    

        dbcon.close()
    except sqlite3.OperationalError as e:
        print(e)

if __name__ == "__main__":
    ppdb()
    click
        