
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

List all authors:

```bash
python ppubdb.py auth-list --name publications.db
```

List all documents:

```bash
python ppubdb.py doc-list --name publications.db
```

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

You can also pass the extracted DOIs directly to `ppubdb.py`, adding each publication to the database through the `doc-from-doi` command.


```bash
python -c 'import csv,sys; [print(row["DOI"]) for row in csv.DictReader(sys.stdin)]' < scopus.csv | xargs -n 1 python ppubdb.py doc-from-doi
```

Technically, the first part of the command reads the CSV file and prints one DOI per line. 
The output is then piped to `xargs`, which takes each DOI and uses it as an argument for `python ppubdb.py doc-from-doi`. 
The option `-n 1` tells `xargs` to execute the command once for each DOI.
