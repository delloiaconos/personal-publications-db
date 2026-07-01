## Project Notes

This file collects practical notes about the internal structure of **Personal Publication DB**. It is intended as a quick reference for understanding the main files in the repository and the current SQLite database model used by the project.

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

