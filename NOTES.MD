## Project Notes
### Repository structure

```text
.
├── db.sql      # SQLite schema used to initialize the database
├── ppubdb.py   # Click-based Python command-line interface
└── README.md   # Project documentation
```

### Database model

The SQLite schema currently contains the following tables:

| Table | Purpose |
| --- | --- |
| `Authors` | Stores author names using first name, last name, and optional middle name. |
| `AuthorIdentifiers` | Stores unique external identifiers for authors. |
| `Documents` | Stores document title, category, and container such as journal, proceedings, or book title. |
| `DocumentIdentifiers` | Stores unique external identifiers for documents, including DOI values. |
| `DocumentAuthors` | Links documents to authors and stores author order. |



## Prepare the Environment 

### Install Requirements

Install the Python dependencies with:

```bash
python -m pip install click requests jinja2
```

Or create a virtual environment first:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install click requests jinja2
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install click requests jinja2
```


## Quick start

Initialize a new database:

```bash
python ppubdb.py db-init --name publications.db
```

Add a publication from a DOI:

```bash
python ppubdb.py doc-from-doi "10.0000/example-doi" ARTICLE --name publications.db
```

List all authors:

```bash
python ppubdb.py auth-list --name publications.db
```

List all documents:

```bash
python ppubdb.py doc-list --name publications.db
```

Collapse duplicate author records into a preferred author record:

```bash
python ppubdb.py auth-collapse 1 2 3 --name publications.db
```

In this example, author records `2` and `3` are replaced by author record `1` in document-author relationships, then the duplicate author records are deleted.



## CLI commands

### `db-init`

Create a new SQLite database using the schema in `db.sql`.

```bash
python ppubdb.py db-init --name publications.db
```

Options:

- `--name`: database filename. Defaults to `publications.db`.

### `doc-from-doi`

Fetch metadata from a DOI and insert the document, DOI identifier, authors, and author order into the database.

```bash
python ppubdb.py doc-from-doi DOI CATEGORY --name publications.db
```

Arguments:

- `DOI`: the document DOI, for example `10.0000/example-doi`.
- `CATEGORY`: a custom category for the document, for example `ARTICLE`, `PREPRINT`, `BOOK_CHAPTER`, or `TALK`.

Options:

- `--name`: database filename. Defaults to `publications.db`.

### `auth-list`

List all authors stored in the database.

```bash
python ppubdb.py auth-list --name publications.db
```

### `doc-list`

List all stored documents ordered by category.

```bash
python ppubdb.py doc-list --name publications.db
```

### `auth-collapse`

Merge multiple duplicate author records into a single preferred author ID.

```bash
python ppubdb.py auth-collapse PREFERRED_AUTHOR_ID DUPLICATE_AUTHOR_ID [DUPLICATE_AUTHOR_ID ...] --name publications.db
```

Example:

```bash
python ppubdb.py auth-collapse 1 4 7 --name publications.db
```

This keeps author `1`, updates document-author links that pointed to authors `4` and `7`, and then removes authors `4` and `7`.

### `db-prune`

Reserved for future database cleanup functionality. The command exists but is not implemented yet.
