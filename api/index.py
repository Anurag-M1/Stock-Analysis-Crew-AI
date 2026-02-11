import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from stock_analysis.crew import StockAnalysisCrew

app = Flask(__name__, static_folder=str(ROOT_DIR), static_url_path="")


@app.get("/")
def root():
    return send_from_directory(ROOT_DIR, "index.html")


@app.get("/api/health")
@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.route("/api/analyze", methods=["GET", "POST"])
@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    ticker_default = os.getenv("COMPANY_STOCK", "AMZN")

    if request.method == "GET":
        ticker = request.args.get("ticker", ticker_default)
    else:
        payload = request.get_json(silent=True) or {}
        ticker = payload.get("ticker", ticker_default)

    ticker = str(ticker).strip().upper()
    if not ticker:
        return jsonify({"ok": False, "error": "ticker is required"}), 400

    inputs = {
        "query": "What is the company you want to analyze?",
        "company_stock": ticker,
    }

    try:
        result = StockAnalysisCrew().crew().kickoff(inputs=inputs)
        return jsonify({"ok": True, "ticker": ticker, "report": str(result)})
    except Exception as exc:
        return jsonify({"ok": False, "ticker": ticker, "error": str(exc)}), 500


def run_local() -> None:
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    run_local()
