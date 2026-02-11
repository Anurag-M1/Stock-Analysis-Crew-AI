import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import html2text
import requests
from sec_api import QueryApi
from dotenv import load_dotenv

load_dotenv()


def _search_news(query: str, limit: int = 5) -> str:
    try:
        rss_url = (
            "https://news.google.com/rss/search?"
            f"q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
        )
        resp = requests.get(rss_url, timeout=20)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        items = root.findall(".//item")[:limit]
        if not items:
            return "No recent news found."
        lines = []
        for item in items:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            lines.append(f"- {title}\n  {link}")
        return "\n".join(lines)
    except Exception as exc:
        return f"News lookup failed: {exc}"


def _latest_filing(ticker: str, form_type: str, sec_api_key: str) -> Optional[dict]:
    try:
        query_api = QueryApi(api_key=sec_api_key)
        query = {
            "query": {
                "query_string": {
                    "query": f'ticker:{ticker} AND formType:"{form_type}"'
                }
            },
            "from": "0",
            "size": "1",
            "sort": [{"filedAt": {"order": "desc"}}],
        }
        filings = query_api.get_filings(query).get("filings", [])
        return filings[0] if filings else None
    except Exception:
        return None


def _filing_text(url: str) -> Optional[str]:
    try:
        headers = {
            "User-Agent": "stock-analysis-crew-ai contact@example.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        converter = html2text.HTML2Text()
        converter.ignore_links = True
        text = converter.handle(resp.text)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return None


def _extract_snippet(text: str, query: str) -> str:
    terms = [t.lower() for t in re.findall(r"[a-zA-Z0-9]{3,}", query)]
    lower = text.lower()
    first_idx = -1
    for term in terms[:10]:
        idx = lower.find(term)
        if idx != -1:
            first_idx = idx if first_idx == -1 else min(first_idx, idx)
    if first_idx == -1:
        return text[:1000]
    start = max(0, first_idx - 250)
    end = min(len(text), first_idx + 900)
    return text[start:end]


def _filing_context(ticker: str, form_type: str, search_query: str) -> str:
    sec_api_key = os.getenv("SEC_API_API_KEY", "").strip()
    if not sec_api_key:
        return f"{form_type}: SEC_API_API_KEY missing."

    filing = _latest_filing(ticker, form_type, sec_api_key)
    if not filing:
        return f"{form_type}: no filing found."

    filing_url = filing.get("linkToFilingDetails", "")
    filed_at = filing.get("filedAt", "N/A")
    if not filing_url:
        return f"{form_type}: filing found but URL missing."

    text = _filing_text(filing_url)
    if not text:
        return f"{form_type}: unable to fetch filing text."

    snippet = _extract_snippet(text, search_query)
    return (
        f"{form_type} filed at {filed_at}\n"
        f"Source: {filing_url}\n"
        f"Snippet:\n{snippet[:1200]}"
    )


def _llm_config() -> tuple[str, str, str]:
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if groq_key:
        return (
            os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/"),
            groq_key,
            os.getenv("MODEL", "llama-3.1-8b-instant"),
        )

    xai_key = os.getenv("XAI_API_KEY", "").strip()
    if xai_key:
        return (
            os.getenv("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/"),
            xai_key,
            os.getenv("XAI_MODEL", "grok-2-latest"),
        )

    raise ValueError("Set GROQ_API_KEY or XAI_API_KEY.")


def _generate_report(ticker: str, context: str) -> str:
    base_url, api_key, model = _llm_config()
    max_tokens = int(os.getenv("MAX_TOKENS", "450"))
    temperature = float(os.getenv("TEMPERATURE", "0.2"))

    system_prompt = (
        "You are a pragmatic stock analyst. "
        "Return concise markdown with sections: Summary, Financial View, Filing View, "
        "Risks, Catalysts, Recommendation (Buy/Hold/Sell with confidence)."
    )
    user_prompt = (
        f"Analyze ticker {ticker} using this context:\n\n{context}\n\n"
        "Keep the answer practical and short."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
        or "No content returned by model."
    )


def run_analysis(ticker: str) -> str:
    ticker = (ticker or os.getenv("COMPANY_STOCK", "AMZN")).strip().upper()
    if not ticker:
        raise ValueError("Ticker is required.")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    news = _search_news(f"{ticker} stock news market sentiment")
    earnings = _search_news(f"{ticker} earnings date guidance")
    filing_query = "MD&A guidance risks cash flow liquidity outlook"
    form_10q = _filing_context(ticker, "10-Q", filing_query)
    form_10k = _filing_context(ticker, "10-K", filing_query)

    context = (
        f"Timestamp: {now}\n"
        f"Ticker: {ticker}\n\n"
        f"Recent News:\n{news}\n\n"
        f"Earnings/Catalysts:\n{earnings}\n\n"
        f"10-Q Context:\n{form_10q}\n\n"
        f"10-K Context:\n{form_10k}\n"
    )

    try:
        return _generate_report(ticker, context)
    except Exception as exc:
        return (
            "LLM generation failed. Returning raw context.\n\n"
            f"Reason: {exc}\n\n"
            f"{context[:5000]}"
        )
