import sqlite3
import requests
import click


@click.group()
def ppdb():
    """Personal Publications Database CLI"""
    pass


@ppdb.command(name='dbinit')
@click.option(
    "--name", "fName",
    default="publications.db",
    type=click.Path(exists=False),
    help="Database name.",

)
def dbi_init(fName):
    """Instanciate a new database."""
    dbcon = sqlite3.connect(fName)
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


@ppdb.command(name='dbprune')
@click.option(
    "--name", "fName",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def dbi_prune(fName):
    """Prune the database."""
    pass

@ppdb.command(name='add-from-doi')
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
    "--name", "fName",
    default="publications.db",
    type=click.Path(exists=True),
    help="Database name.",
)
def doc_add_from_doi( doi:str, category:str, fName:str):
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

    dbcon = sqlite3.connect(fName)
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

if __name__ == "__main__":
    ppdb()
    click
        