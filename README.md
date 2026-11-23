# Prompt-to-App Builder

Describe a web app in plain language, and planner, architect and coder agents create its files. Progress and code appear in a browser dashboard.

## Credit

The planner, architect and coder pipeline is based on [coder-buddy](https://github.com/codebasics/coder-buddy) by Codebasics (copyright Codebasics Inc., all rights reserved). Most of the agent state, prompts and file tools come from that project.

**What I added:**

- Web dashboard to enter a prompt, follow progress, and view and edit generated files
- FastAPI server that runs generation in the background
- Live status and log tracking for each agent
- Combined command-line and dashboard launcher
- A small standalone Groq chat script

## Run

Requires Python 3.14+, [uv](https://docs.astral.sh/uv/) and a [Groq](https://console.groq.com/keys) API key.

```bash
uv sync
echo "GROQ_API_KEY=your-key" > .env
uv run python main.py                        # dashboard at http://127.0.0.1:8000
uv run python main.py --prompt "a todo app"  # command line
```

Generated files go to `generated_project/`. Run it locally only: the server has no authentication.
