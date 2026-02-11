import os
import re
from typing import Optional

import html2text
import requests
from sec_api import QueryApi


class _SECFilingTool:
    form_type: str = ""
    _max_chars: int = 1200

    def _run(self, search_query: str, stock_name: str = "") -> str:
        ticker = (stock_name or os.getenv("COMPANY_STOCK", "")).strip().upper()
        if not ticker:
            return "Ticker is required. Provide `stock_name` or set COMPANY_STOCK."

        api_key = os.getenv("SEC_API_API_KEY", "").strip()
        if not api_key:
            return "SEC_API_API_KEY is missing."

        filing = self._get_latest_filing(ticker, api_key)
        if not filing:
            return f"No {self.form_type} filing found for {ticker}."

        filing_url = filing.get("linkToFilingDetails", "")
        if not filing_url:
            return f"{self.form_type} filing found for {ticker}, but filing URL is missing."

        text = self._fetch_filing_text(filing_url)
        if not text:
            return f"Unable to fetch {self.form_type} filing text for {ticker}."

        snippet = self._extract_relevant_snippet(text, search_query)
        response = (
            f"Ticker: {ticker}\n"
            f"Form: {self.form_type}\n"
            f"Filed At: {filing.get('filedAt', 'N/A')}\n"
            f"Source: {filing_url}\n\n"
            f"Relevant Content:\n{snippet}"
        )
        if len(response) > self._max_chars:
            return response[: self._max_chars] + "\n\n[truncated]"
        return response

    def _get_latest_filing(self, ticker: str, api_key: str) -> Optional[dict]:
        try:
            query_api = QueryApi(api_key=api_key)
            query = {
                "query": {
                    "query_string": {
                        "query": f'ticker:{ticker} AND formType:"{self.form_type}"'
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

    def _fetch_filing_text(self, filing_url: str) -> Optional[str]:
        try:
            headers = {
                "User-Agent": "stock-analysis-crew-ai contact@example.com",
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov",
            }
            response = requests.get(filing_url, headers=headers, timeout=30)
            response.raise_for_status()
            converter = html2text.HTML2Text()
            converter.ignore_links = True
            text = converter.handle(response.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception:
            return None

    def _extract_relevant_snippet(self, text: str, query: str) -> str:
        lower_text = text.lower()
        terms = [t.lower() for t in re.findall(r"[a-zA-Z0-9]{3,}", query)]
        best_index = -1

        for term in terms[:8]:
            idx = lower_text.find(term)
            if idx != -1 and (best_index == -1 or idx < best_index):
                best_index = idx

        if best_index == -1:
            return text[:900]

        start = max(0, best_index - 250)
        end = min(len(text), best_index + 850)
        return text[start:end]


class SEC10QTool(_SECFilingTool):
    name: str = "search_in_the_specified_10_q_form"
    description: str = (
        "Search relevant information in the latest SEC 10-Q filing for a ticker."
    )
    form_type: str = "10-Q"


class SEC10KTool(_SECFilingTool):
    name: str = "search_in_the_specified_10_k_form"
    description: str = (
        "Search relevant information in the latest SEC 10-K filing for a ticker."
    )
    form_type: str = "10-K"
