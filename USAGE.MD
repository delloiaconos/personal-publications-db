
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

All command failures are written to standard error and return a non-zero exit
code. SQLite failures use the common `Error: Database error: ...` format.

Initialize a new database:

```bash
python ppubdb.py db-init --name publications.db
```

Add a publication from a DOI:

```bash
python ppubdb.py doc-from-doi "10.0000/example-doi" ARTICLE --name publications.db
```

The DOI may also be entered as `doi:10....` or as a `https://doi.org/...`
URL. The command validates the metadata response, rejects duplicate DOIs, and
leaves the database unchanged if any insertion step fails.

List all authors:

```bash
python ppubdb.py auth-list --name publications.db
```

List all documents:

```bash
python ppubdb.py doc-list --name publications.db
```

Export all documents with a specific tag to Markdown:

```bash
python ppubdb.py doc-export-tag important \
  --name publications.db \
  --output important.md
```

Without `--output`, the Markdown is written to standard output.

Remove orphaned relationship and identifier records, verify referential
integrity, and compact the database file:

```bash
python ppubdb.py db-prune --name publications.db
```

Collapse duplicate author records into a preferred author record:

```bash
python ppubdb.py auth-collapse 1 2 3 --name publications.db
```

In this example, document relationships and identifiers belonging to authors `2`
and `3` are transferred to author `1`, then the duplicate author records are
deleted. Existing relationships to author `1` are preserved.

## Development 

### Generating Documentation

```bash
click-docs ppubdb.py \
  --command-name ppdb \
  --program-name ppubdb \
  --output MANUAL.MD \
  --list-subcommands
```


### ER Diagram Generation

In order to generate the ER diagram available in the documentation, I use (sqlmermaid)[https://github.com/endremborza/sqlmermaid], a python tool that generate Mermaid ER diagrams from any SQLAlchemy-supported database. 

You can install `sqlmermaid` within your environemnt using the following command:
```bash
pip install sqlmermaid
```

I personally start from a clean database and then generate the er diagram in a temporary file (the tool checks for file extension):
```bash
rm publications.db 
ppubdb db-init
sqlmermaid sqlite:///publications.db -o erdiagram.md
```

## Usefoul Commands

### Manage `scopus.csv`

Scopus can export a full list of your publications. To keep the exported file clean and easy to process, I suggest selecting only the minimum required information, such as the DOI, which is essential, and the title. Then export the file in `.csv` format. Once the file has been downloaded, you can use the following command to extract the list of DOIs.


```bash
python -c 'import csv,sys; [print(row["DOI"]) for row in csv.DictReader(sys.stdin)]' < scopus.csv
```

You can save the extracted DOIs to a text file and pass it directly to
`doc-from-doi`. The file must contain one DOI per line; empty lines are ignored.


```bash
python -c 'import csv,sys; [print(row["DOI"]) for row in csv.DictReader(sys.stdin)]' < scopus.csv > dois.txt
python ppubdb.py doc-from-doi dois.txt ARTICLE --name publications.db
```

The first command reads the CSV file and writes one DOI per line. The second
imports all those publications with the `ARTICLE` category. The batch is
atomic: if one DOI cannot be processed, no publication from that invocation is
added.
