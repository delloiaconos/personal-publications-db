# ppubdb

Personal Publications Database CLI

**Usage:**

```text
ppubdb [OPTIONS] COMMAND [ARGS]...
```

**Options:**

```text
  --help  Show this message and exit.
```

**Subcommands:**

- [auth-collapse](#auth-collapse): Merge source authors into a target without leaving orphaned records.
- [auth-list](#auth-list): List all the authors with their IDs.
- [category-list](#category-list): List all the documents categories.
- [db-init](#db-init): Instanciate a new database.
- [db-prune](#db-prune): Prune the database.
- [doc-from-doi](#doc-from-doi): Add a document using its DOI.
- [doc-list](#doc-list): List all the documents with their IDs.

## auth-collapse

Merge source authors into a target without leaving orphaned records.

**Usage:**

```text
ppubdb auth-collapse [OPTIONS] IDAUTHOR [IDS]...
```

**Options:**

```text
  --name PATH  Database name.
  --help       Show this message and exit.
```

## auth-list

List all the authors with their IDs.

**Usage:**

```text
ppubdb auth-list [OPTIONS]
```

**Options:**

```text
  [SURNAME|FIRSTNAME], --sort [surname|firstname|middlename]
                                  Sort order for the author list.
  --name PATH                     Database name.
  --stats                         Enable verbose output.
  --help                          Show this message and exit.
```

## category-list

List all the documents categories.

**Usage:**

```text
ppubdb category-list [OPTIONS]
```

**Options:**

```text
  --name PATH  Database name.
  --stats      Enable verbose output.
  --help       Show this message and exit.
```

## db-init

Instanciate a new database.

**Usage:**

```text
ppubdb db-init [OPTIONS]
```

**Options:**

```text
  --name PATH  Database name.
  --help       Show this message and exit.
```

## db-prune

Prune the database.

**Usage:**

```text
ppubdb db-prune [OPTIONS]
```

**Options:**

```text
  --name PATH  Database name.
  --help       Show this message and exit.
```

## doc-from-doi

Add a document using its DOI.

**Usage:**

```text
ppubdb doc-from-doi [OPTIONS] DOI [CATEGORY]
```

**Options:**

```text
  --name PATH  Database name.
  --help       Show this message and exit.
```

## doc-list

List all the documents with their IDs.

**Usage:**

```text
ppubdb doc-list [OPTIONS]
```

**Options:**

```text
  --category TEXT  Filter documents by category.
  --name PATH      Database name.
  --help           Show this message and exit.
```
