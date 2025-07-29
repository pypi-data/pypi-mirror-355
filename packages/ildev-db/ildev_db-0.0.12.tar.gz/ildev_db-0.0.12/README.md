# ildev_db

A reusable Python module that integrates SQLite, SQLAlchemy (async), and the repository pattern.

## Features

- Async database access using SQLite and SQLAlchemy.
- Implements the repository pattern.
- Fully tested and reusable.


## Installation

```bash
pip install ildev_db
```

## Usage locally
```
python -m venv local-venv
./local-venv/Scripts/activate
pip install -r requirements.txt 
OR
pip install .[build]      # Install build tools
pip install .[test]       # Install test tools
pip install .[dev]        # Install all dev tools

if python.exe access denied: Remove-Item -Recurse -Force \ildev_db\local-venv
```