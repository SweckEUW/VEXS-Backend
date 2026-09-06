# VEXS-Backend

Visual Execution System Backend Server.

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) installed

## Install UV

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Setup & Install dependencies

```bash
# Install dependencies and create venv
uv sync
```

`uv sync` automatically creates the virtual environment and installs all dependencies defined in `pyproject.toml`.

## Environment Variables

The backend uses `pydantic-settings` for configuration. Do not hardcode credentials. 
Copy the example environment file and fill in your ShotGrid credentials:

Required variables in `.env`:
- `SERVER_PATH`
- `SCRIPT_NAME`
- `SCRIPT_KEY`
- `SHOTGRID_PROJECT_ID`
- `GRAPH_ENTITY`

## Start the project

In the project root folder run:

```bash
# Start server with auto-reload
uv run uvicorn src.main:app --reload
```

The API is then available at:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Development

To add new dependencies to the project, use `uv add` instead of `pip install`:

```bash
# Add new package
uv add <package_name>
```