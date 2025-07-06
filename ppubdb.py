import sqlite3
import requests
import click

def create_database(dbcon):
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

def fetch_publication_from_doi( doi, category='DOC'):
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

if __name__ == "__main__":
    # Connect to the SQLite database (or create it if it doesn't exist)
    dbcon = sqlite3.connect('publications.db')
    
    # Create a cursor object to interact with the database
    dbcur = dbcon.cursor()

    create_database(dbcon)
    fetch_publication_from_doi("10.1007/978-3-030-37558-4_50")
    fetch_publication_from_doi("10.1007/978-3-030-37558-4_51")
    dbcon.close()    