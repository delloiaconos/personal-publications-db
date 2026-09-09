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
- [db-init](#db-init): Instantiate a new database.
- [db-prune](#db-prune): Remove orphaned records and compact the database.
- [doc-from-doi](#doc-from-doi): Add a document using its DOI.
- [doc-export-tag](#doc-export-tag): Export documents with a tag using a Jinja2 template.
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
  --sort [SURNAME|FIRSTNAME|MIDDLENAME]
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

Instantiate a new database.

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

Remove orphaned records and compact the database.

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

## doc-export-tag

Export all documents with a tag using a Jinja2 template.

**Usage:**

```text
ppubdb doc-export-tag [OPTIONS] TAG
```

**Options:**

```text
  --template TEXT  Jinja2 template name or local path.  [default:
                   document_by_tag.md.j2]
  --output FILE    Rendered output path; '-' writes to standard output.
  --name PATH      Database name.
  --help           Show this message and exit.
```

The template is resolved first as a file in the current directory and then by
name in the templates bundled with `ppubdb`. The Jinja2 context contains `tag`
and `documents`. Each document provides `id`, `title`, `category`, `container`,
and `authors`. Authors are ordered by their publication order and provide `id`,
`first_name`, `middle_name`, `last_name`, and `order`.

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
