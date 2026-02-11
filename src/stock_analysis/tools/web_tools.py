import os
import re
from urllib.parse import quote
import xml.etree.ElementTree as ET
from typing import Optional

import html2text
import requests


class BraveSearchAliasTool:
    name: str = "brave_search"
    description: str = (
        "Search the web for recent information. Input must be a `query` string."
    )
    _max_chars: int = 700
    _serper_enabled: Optional[bool] = None

    def _run(self, query: str) -> str:
        query = (query or "").strip()
        if not query:
            return "Query is required."
        lines = [f"Query: {query}"]
        if self._serper_available():
            try:
                result = self._serper_search(query)
                organic = result.get("organic", [])[:3]
                if organic:
                    lines.append("Top web results:")
                    for item in organic:
                        title = item.get("title", "").strip()
                        lines.append(f"- {title}")

                news = result.get("news", [])[:3]
                if news:
                    lines.append("Top news results:")
                    for item in news:
                        title = item.get("title", "").strip()
                        lines.append(f"- {title}")
            except Exception as e:
                self._serper_enabled = False
                lines.append(f"Serper unavailable ({e}). Using fallback search.")
                lines.extend(self._fallback_search(query))
        else:
            lines.append("Serper unavailable (auth failed, missing key, or service issue). Using fallback search.")
            lines.extend(self._fallback_search(query))

        output = "\n".join(lines).strip()
        if len(output) > self._max_chars:
            return output[: self._max_chars] + "\n\n[truncated]"
        return output

    def _serper_available(self) -> bool:
        if self._serper_enabled is not None:
            return self._serper_enabled

        # Serper is opt-in to prevent hard failures from invalid/blocked keys.
        use_serper = os.getenv("USE_SERPER", "false").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        if not use_serper:
            self._serper_enabled = False
            return False

        key = os.getenv("SERPER_API_KEY", "").strip()
        if not key or key.upper() == "KEY":
            self._serper_enabled = False
            return False

        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
                json={"q": "test"},
                timeout=12,
            )
            self._serper_enabled = resp.status_code == 200
        except Exception:
            self._serper_enabled = False

        return self._serper_enabled

    def _serper_search(self, query: str) -> dict:
        key = os.getenv("SERPER_API_KEY", "").strip()
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def _fallback_search(self, query: str) -> list[str]:
        lines = []
        # 1) Try Google News RSS (no API key required).
        try:
            rss_url = (
                "https://news.google.com/rss/search?"
                f"q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
            )
            rss_resp = requests.get(rss_url, timeout=20)
            rss_resp.raise_for_status()
            root = ET.fromstring(rss_resp.text)
            items = root.findall(".//item")
            if items:
                lines.append("Fallback news results:")
                for item in items[:4]:
                    title = (item.findtext("title") or "").strip()
                    lines.append(f"- {title}")
                return lines
        except Exception:
            pass

        # 2) Fallback to DuckDuckGo instant-answer API.
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": 1, "no_redirect": 1}
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        abstract = (data.get("AbstractText") or "").strip()
        abstract_url = (data.get("AbstractURL") or "").strip()
        if abstract:
            lines.append("Fallback abstract:")
            lines.append(f"- {abstract}")
            if abstract_url:
                lines.append(f"  Source: {abstract_url}")

        related = data.get("RelatedTopics", [])
        flat_related = []
        for item in related:
            if isinstance(item, dict) and "Text" in item:
                flat_related.append(item)
            elif isinstance(item, dict) and "Topics" in item:
                for sub in item.get("Topics", []):
                    if isinstance(sub, dict) and "Text" in sub:
                        flat_related.append(sub)

        if flat_related:
            lines.append("Fallback related topics:")
            for item in flat_related[:4]:
                text = (item.get("Text") or "").strip()
                lines.append(f"- {text}")

        if not lines:
            lines.append("Fallback search returned limited data.")
        return lines


class ReadWebsiteContentAliasTool:
    name: str = "read_website_content"
    description: str = (
        "Fetch readable text from a webpage URL. Input must be a `website_url` string."
    )
    _max_chars: int = 900

    def _run(self, website_url: str) -> str:
        try:
            response = requests.get(website_url, timeout=20)
            response.raise_for_status()
            converter = html2text.HTML2Text()
            converter.ignore_links = False
            text = converter.handle(response.text)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()

            if len(text) > self._max_chars:
                return text[: self._max_chars] + "\n\n[truncated]"
            return text
        except Exception as e:
            return f"Unable to read website content from {website_url}: {e}"
