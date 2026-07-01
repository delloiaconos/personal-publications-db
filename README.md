# Personal Publication DB

_Personal Publication DB_ is a small Python command-line utility for managing your own publications, references, and publication metadata in a local SQLite database.

## Description

The project is designed around a simple idea: a publication list is personal. DOI metadata is useful, but it is not always exactly how you want your name, your co-authors, unpublished works, or custom categories to appear in a CV, personal website, GitHub profile, academic page, or other publication output.

Design notes and usage can be found in [NOTES](NOTES.MD).

### Motivation

This project was created to solve a personal but common problem: author names are sometimes misspelled, formatted inconsistently, or represented differently across publication databases. For example, a DOI record may contain a version of your name that is technically valid but not the one you want to display on your curriculum vitae, website, or personal academic profile.

Personal Publication DB is not intended to duplicate full reference managers or bibliography tools. Instead, it focuses on maintaining a curated, local, personal publication database where you can:

- import publication metadata from a DOI;
- correct or personalize author names;
- merge duplicate author records;
- include unpublished or not-yet-indexed works;
- organize publications by category;
- eventually render custom publication lists using Jinja2 templates.

### Design philosophy

Personal Publication DB treats DOI metadata as a starting point, not as the final source of truth. Imported data can be corrected, curated, and adapted to match how you want your work to appear publicly.

This is especially useful when:

- your name appears with different spellings across systems;
- your name contains accents, initials, particles, or multiple surnames;
- DOI metadata uses inconsistent author formatting;
- you want to include works that do not have a DOI yet;
- you need different citation formats for different contexts.


## Features

This project is in an early development stage. The current implementation provides a Python CLI backed by SQLite. DOI import, author listing, publication listing, and basic author merging are already present. Template-based export with Jinja2 is part of the project scope and roadmap.

### Implemented

- Create a new SQLite publication database.
- Import a document from a DOI using DOI metadata.
- Store documents, document identifiers, authors, author identifiers, and document-author relationships.
- Preserve author order for each document.
- List all authors in the local database.
- List all stored documents.
- Collapse duplicate author records into a preferred author entry.

### Planned

- Export formatted references using Jinja2 templates.
- Create custom templates for CVs, websites, GitHub profile pages, and academic pages.
- Add manual publication entry for unpublished or preprint works.
- Improve database maintenance commands.
- Add richer author personalization, such as preferred display names and initials.
- Add tests and packaging metadata.

### Long Term Planning
The long-term goal is to generate publication lists from the SQLite database using Jinja2 templates. A template-based workflow will make it possible to create multiple outputs from the same curated data source, such as:

- a compact CV publication section;
- a full academic publication list;
- a Markdown publication list for GitHub;
- an HTML block for a personal website;
- custom formats for grants, reports, or institutional pages.

## License

This project is licensed under the **GNU General Public License Version 3, 29 June 2007**.

See the [LICENSE](./LICENSE) file for the full license text.

## Contributing

Contributions are welcome.

You can contribute by:

- reporting bugs or unexpected behavior;
- suggesting new features or improvements;
- improving the documentation;
- adding tests;
- improving the CLI commands;
- extending DOI metadata handling;
- creating or improving Jinja2 templates for publication export.

Before submitting a contribution, please open an issue or discussion to describe the proposed change, especially for larger modifications.

To contribute code:

1. Fork the repository.
2. Create a dedicated branch for your changes.
3. Make your changes with clear and focused commits.
4. Test your changes locally.
5. Open a pull request describing what was changed and why.

Please keep contributions aligned with the goal of the project: a simple, personal, local, and customizable publication database.

