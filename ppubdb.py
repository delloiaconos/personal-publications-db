import sqlite3

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

if __name__ == "__main__":
    # Connect to the SQLite database (or create it if it doesn't exist)
    dbcon = sqlite3.connect('publications.db')
    
    # Create a cursor object to interact with the database
    dbcur = dbcon.cursor()

    create_database(dbcon)
        
    dbcon.close()    