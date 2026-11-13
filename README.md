# Smart File Organizer

A lightweight Python CLI tool that sorts cluttered folders such as `Downloads` into clean category directories without external runtime dependencies.

## Features

- Categorizes files by extension (`Images`, `Documents`, `Archives`, `Audio`, `Video`, `Code`, `Installers`, and `Other`).
- Protects unfinished browser downloads (`.crdownload`, `.part`, `.tmp`, `.download`) and OS metadata files (`desktop.ini`, `.DS_Store`, `Thumbs.db`).
- Prevents accidental overwrites by renaming colliding files (`report.pdf` becomes `report (1).pdf`).
- Supports `--dry-run` previews before touching any files.
- Groups files by modification month (`YYYY-MM`) with `--by-date`.
- Reverts the previous run with `--undo` and removes empty folders created during sorting.
- Accepts custom rules via a JSON config file.

## Requirements

- Python 3.10 or newer
- `pytest` (only needed to run the test suite)

## Installation

Clone the repository and install it in editable mode:

```bash
git clone https://github.com/rus1117/smart-file-organizer.git
cd smart-file-organizer
pip install -e .
```

You can also run the tool directly without installing by pointing `PYTHONPATH=src` and executing `python -m smart_organizer`.

## Usage

Preview changes in your default `~/Downloads` folder:

```bash
smart-organizer --dry-run
```

Sort a specific folder and group files into monthly subfolders:

```bash
smart-organizer ~/Downloads --by-date --verbose
```

Use custom category rules from [config.example.json](config.example.json):

```bash
smart-organizer ~/Downloads --config config.example.json
```

Undo the last organization run in a directory:

```bash
smart-organizer ~/Downloads --undo
```

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
