# Poetry project setup

Poetry manages project dependencies, virtual environments, and packaging for
Python. This guide covers installation, dependency setup, and common commands
for `streamlit-dividend-dashboard`.

## Step 1: Install Poetry

On **macOS**, install Poetry with Homebrew:

```bash
brew install poetry
```

On **Windows**, install with pip:

```bash
pip install poetry
```

## Step 2: Navigate to project directory

```bash
cd streamlit-dividend-dashboard
```

## Step 3: Install project dependencies

Install all dependencies defined in `pyproject.toml`:

```bash
poetry install
```

This creates a virtual environment and installs:

- **Core dependencies**: `pandas`, `streamlit`, `plotly`, `streamlit-elements`,
  `pydantic-settings`
- **Dev dependencies**: `pytest`, `pytest-cov`, `pytest-mock`, `pytest-asyncio`,
  `pytest-xdist`, `hypothesis`, `freezegun`, `pytest-benchmark`, `mypy`, `ruff`

## Step 4: Run the app

```bash
poetry run streamlit run main.py
```

## Step 5: Run tests

```bash
poetry run pytest
```

## Common Poetry commands

| Command | Description |
|---|---|
| `poetry add package-name` | Add a runtime dependency |
| `poetry add --group dev package-name` | Add a dev dependency |
| `poetry update` | Update all dependencies |
| `poetry show` | List installed packages |
| `poetry remove package-name` | Remove a dependency |
| `poetry show --outdated` | List outdated packages |

## Code quality

Run linting with auto-fix and formatting using Ruff:

```bash
poetry run ruff check --fix .
poetry run ruff format .
```