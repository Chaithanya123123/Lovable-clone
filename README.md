# Lovable Clone

An experimental AI web app builder inspired by Lovable. It turns a natural-language prompt into a small generated web project using a Groq-backed LangGraph agent pipeline.

## What It Does

- Accepts an app idea from the CLI or browser dashboard.
- Uses a planner agent to turn the prompt into a structured project plan.
- Uses an architect agent to break the plan into file-level implementation tasks.
- Uses a coder agent with file tools to write the generated app into `generated_project/`.
- Serves the generated app at `/preview/index.html`.
- Lets you inspect and edit generated files from the dashboard.

## Tech Stack

- Python 3.14+
- FastAPI
- Uvicorn
- LangChain
- LangGraph
- Groq chat models
- Plain HTML, CSS, and JavaScript dashboard

## Requirements

- Python matching `pyproject.toml`
- `uv` for dependency management
- A Groq API key

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

## Setup

```bash
uv sync
```

## Run The Dashboard

```bash
uv run python main.py
```

Then open:

```text
http://127.0.0.1:8000
```

You can also choose a host or port:

```bash
uv run python main.py --host 0.0.0.0 --port 8000
```

## Run From The CLI

```bash
uv run python main.py --prompt "Build a colorful todo app in HTML, CSS, and JavaScript"
```

The generated files are written to:

```text
generated_project/
```

## Project Structure

```text
.
|-- agent/
|   |-- graph.py       # LangGraph planner, architect, and coder workflow
|   |-- prompts.py     # Agent prompts
|   |-- states.py      # Pydantic state models
|   |-- status.py      # Status and log file helpers
|   `-- tools.py       # File and command tools for generated_project
|-- dashboard_assets/
|   `-- index.html     # Browser dashboard
|-- agent_server.py    # FastAPI server and API routes
|-- chatbot.py         # Simple Groq chatbot test script
|-- main.py            # CLI and dashboard entry point
|-- pyproject.toml
`-- README.md
```

## API Routes

- `POST /api/generate` starts app generation.
- `GET /api/status` returns generation phase, logs, and progress.
- `GET /api/files` lists generated files.
- `GET /api/file?path=...` reads a generated file.
- `POST /api/save-file` saves edits to a generated file.
- `GET /preview/index.html` serves the generated app preview.
