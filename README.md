# Stock Analysis Crew AI

Multi-agent stock analysis project built with CrewAI to generate a research-backed stock recommendation report.

## Author
- **Anurag Kumar Singh**
- GitHub: [anurag-m1](https://github.com/anurag-m1)

## Overview
This project runs a sequential crew of agents that:
1. Collect recent stock/news context
2. Analyze financial metrics
3. Review SEC 10-Q and 10-K filings
4. Produce an investment recommendation

The project is configured for **online LLM providers only** (Groq/xAI).

## Features
- Multi-agent workflow with CrewAI
- Online LLM support:
  - Groq (default)
  - xAI/Grok (fallback)
- SEC filing lookup and semantic search
- Safe math/calculator tool for ratio/metric operations
- Structured agent/task configs in YAML
- Low-token defaults to avoid Groq TPM/413 failures

## Tech Stack
- Python 3.12
- [CrewAI](https://github.com/crewAIInc/crewAI)
- CrewAI Tools
- Poetry
- SEC API (`sec-api`)
- HTML parsing (`html2text`)

## Project Structure
```text
api/
  index.py                # Vercel serverless API (health + analyze)
index.html               # Simple frontend UI
styles.css               # Frontend styles
app.js                   # Frontend logic (calls /api/analyze)
src/stock_analysis/
  main.py                 # Entry point
  crew.py                 # Crew, agents, LLM provider selection
  config/
    agents.yaml           # Agent roles/goals/backstories
    tasks.yaml            # Task descriptions + expected outputs
  tools/
    calculator_tool.py    # Safe expression calculator
    sec_tools.py          # SEC 10-Q/10-K retrieval + RAG search
vercel.json              # Vercel function runtime config
requirements.txt         # Vercel Python dependencies
```

## Agent & Task Flow
### Agents
- `research_analyst`
- `financial_analyst`
- `investment_advisor`

### Tasks (sequential)
- `research`
- `financial_analysis`
- `filings_analysis`
- `recommend`

## Prerequisites
- Python `>=3.12, <=3.13`
- pip
- Poetry

## Environment Configuration
Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

### Required variables
| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` or `XAI_API_KEY` | Yes (at least one) | LLM access |
| `MODEL` | Recommended | Model name for Groq path |
| `SERPER_API_KEY` | Optional | Serper search (disabled by default) |
| `USE_SERPER` | Optional | `true` to enable Serper, else fallback search is used |
| `BROWSERLESS_API_KEY` | Recommended | Browser/scrape tool support |
| `SEC_API_API_KEY` | Yes for filings quality | SEC 10-Q/10-K fetch |
| `MAX_TOKENS` | Recommended | Per-call output cap (default `280`) |
| `AGENT_MAX_ITER` | Recommended | Max reasoning loops per agent (default `4`) |

### Provider behavior
- If `GROQ_API_KEY` is set, crew uses Groq-compatible endpoint (`GROQ_BASE_URL`).
- Else if `XAI_API_KEY` is set, crew uses xAI endpoint (`XAI_BASE_URL`).
- If neither is set, startup fails with a clear error.
- Serper is opt-in. With `USE_SERPER=false`, web search uses fallback sources and avoids Serper 403 failures.

## Installation
From project root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install poetry platformdirs
poetry env use "$(pwd)/.venv/bin/python"
poetry install --no-root
```

## Run
```bash
poetry run python src/stock_analysis/main.py
```

The script prints the final report in terminal.

Run with another ticker:
```bash
COMPANY_STOCK=TSLA poetry run python src/stock_analysis/main.py
```

## Web UI (HTML/CSS/JS)
A simple UI is included at `/` and calls `/api/analyze`.

### On Vercel
- Open: `https://<your-project>.vercel.app/`
- Enter ticker and click **Analyze**.

### Local preview with API
Run directly with Flask:
```bash
source .venv/bin/activate
poetry install --no-root
poetry run python api/index.py
```
Then open `http://localhost:5000`.

Optional Vercel emulation:
```bash
npm i -g vercel
vercel dev
```
Then open `http://localhost:3000`.

## Deploy on Vercel
This repo is deployable on Vercel as a Python serverless API.

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Vercel deployment support"
git push origin main
```

### 2. Import in Vercel
1. Open Vercel dashboard.
2. Click **Add New Project**.
3. Import your GitHub repository.
4. Keep root directory as project root.
5. Framework preset can stay as **Other**.

### 3. Set environment variables in Vercel
Add the same keys you use locally:
- `GROQ_API_KEY`
- `MODEL`
- `GROQ_BASE_URL`
- `MAX_TOKENS`
- `TEMPERATURE`
- `AGENT_MAX_ITER`
- `COMPANY_STOCK`
- `SEC_API_API_KEY`
- `SERPER_API_KEY` (optional)
- `USE_SERPER` (optional, default false)
- `BROWSERLESS_API_KEY` (optional)
- `CREWAI_TRACING_ENABLED` (optional)

### 4. Deploy
Click **Deploy**. Vercel will install from `requirements.txt` and expose the API.

### 5. Test endpoints
- Frontend:
  - `GET https://<your-project>.vercel.app/`
- Health:
  - `GET https://<your-project>.vercel.app/api/health`
- Analyze (GET):
  - `GET https://<your-project>.vercel.app/api/analyze?ticker=AMZN`
- Analyze (POST):
```bash
curl -X POST "https://<your-project>.vercel.app/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AMZN"}'
```

### Notes for Vercel
- `vercel.json` sets function max duration to 60s.
- If a run exceeds serverless timeout, reduce model/tool usage or use a long-running host (Railway/Render/Fly.io).
- SEC tool vector DB is configured to use `/tmp` for serverless compatibility.

## Train Mode
`train()` exists in `src/stock_analysis/main.py` but is not wired to CLI argument parsing in `__main__`. If you want to use training, call it explicitly (or add your own CLI wrapper).

## Change Target Stock
Default stock is loaded from `.env` as `COMPANY_STOCK` (default `AMZN`).

## Troubleshooting
### `ImportError: cannot import name 'BaseTool' from 'crewai_tools'`
Use:
- `from crewai.tools import BaseTool`

### Pydantic schema errors (`model_json_schema` / `pydantic.v1`)
Use Pydantic v2 imports in tool schemas:
- `from pydantic import BaseModel, Field`

### `OPENAI_API_KEY` requested unexpectedly
Some old CrewAI tools require OpenAI embeddings by default. This project uses ONNX embedding config in SEC tools to avoid OpenAI-only embedding dependency.

### Groq rate limit errors
If you hit token/day limit:
- wait for reset window, or
- switch to a smaller model in `.env` (for example an 8B model), or
- upgrade Groq plan.

### `Error code: 413` (request too large / TPM limit)
This means a single request exceeded Groq token-per-minute budget.
Use these safe defaults:
- `MAX_TOKENS=280`
- `AGENT_MAX_ITER=4`
- keep prompts concise
- avoid enabling too many tools per agent

### SEC tool returns no/poor filing content
Check:
- `SEC_API_API_KEY` is valid
- ticker exists and has recent filings
- SEC/network is reachable

### Serper `403 Unauthorized`
If Serper still returns 403 even with a key:
- keep `USE_SERPER=false` (default) and use fallback search
- re-check key permissions in Serper dashboard before setting `USE_SERPER=true`

## Security Notes
- Never commit real API keys.
- Keep `.env` local and private.
- Rotate keys if they were ever exposed.

## License
MIT
