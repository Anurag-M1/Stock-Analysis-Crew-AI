# Stock Analysis Crew AI

Stock analysis project built with CrewAI.
It collects market/news context, reviews financial signals and SEC filings, then generates an investment recommendation.

## Author
- **Anurag Kumar Singh**
- GitHub: [Anurag-M1](https://github.com/anurag-m1)
- live : https://stock-analysis-crew-ai.vercel.app

## What This Project Includes
- Multi-agent stock analysis workflow
- Local web UI (HTML/CSS/JS)
- Local API endpoint for running analysis from UI
- Groq/xAI based LLM support

## Project Structure
```text
api/
  index.py
src/stock_analysis/
  main.py
  crew.py
  config/
  tools/
index.html
styles.css
app.js
```

## Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --no-root
```

## Environment
Create `.env` from `.env.example` and fill keys:

```bash
cp .env.example .env
```

Minimum required:
- `GROQ_API_KEY` (or `XAI_API_KEY`)
- `SEC_API_API_KEY`

Useful defaults:
- `MODEL=llama-3.1-8b-instant`
- `MAX_TOKENS=280`
- `AGENT_MAX_ITER=4`
- `COMPANY_STOCK=AMZN`

## Run In Browser (Recommended)
```bash
source .venv/bin/activate
PORT=5050 poetry run python api/index.py
```

Open:
- `http://localhost:5050`

Health/API:
- `http://localhost:5050/api/health`
- `http://localhost:5050/api/analyze?ticker=AMZN`

## Run In Terminal (Optional)
```bash
source .venv/bin/activate
poetry run python src/stock_analysis/main.py
```

## Notes
- If port `5000` is busy, run on another port (example: `PORT=5050`).
- `USE_SERPER=false` keeps search on fallback mode if Serper key is not working.
- Never commit real API keys.
