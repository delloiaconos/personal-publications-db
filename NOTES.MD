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

The SQLite database is currently structured like:

```mermaid
erDiagram
  "AuthorIdentifiers" {    
    INTEGER idAuthor FK     
    TEXT IdentifierType      
    TEXT AuthorIdentifier  
  }
  "Authors" {    
    INTEGER idAuthor PK     
    TEXT FirstName      
    TEXT LastName      
    TEXT MiddleName  
  }
  "DocumentAuthors" {    
    INTEGER idDocument PK     
    INTEGER idAuthor PK     
    INTEGER AuthOrder  
  }
  "Documents" {    
    INTEGER idDocument PK     
    BLOB Title  "in index: idxDocument_Title"    
    TEXT Category  "in index: idxDocument_Category"    
    TEXT Container  "in index: idxDocument_Container"
  }
  "DocumentIdentifiers" {    
    INTEGER idDocument PK     
    TEXT IdentifierType PK "in index: idxDocumentIdentifiers_IdentifierType"    
    TEXT DocumentIdentifier  
  }
  "DocumentKeywords" {    
    INTEGER idDocument PK     
    TEXT Keyword PK "in index: idxDocumentKeywords_Keyword"
  }
  "DocumentTags" {    
    INTEGER idDocument PK     
    TEXT DocumentTag PK "in index: idxDocumentTags_DocumentTag"
  }
  "AuthorIdentifiers" ||--|{ "Authors" : "idAuthor -> idAuthor"
  "DocumentAuthors" ||--|{ "Authors" : "idAuthor -> idAuthor"
  "DocumentAuthors" ||--|{ "Documents" : "idDocument -> idDocument"
  "DocumentIdentifiers" ||--|{ "Documents" : "idDocument -> idDocument"
  "DocumentKeywords" ||--|{ "Documents" : "idDocument -> idDocument"
  "DocumentTags" ||--|{ "Documents" : "idDocument -> idDocument"
```
