import os
import re
from typing import Any, Optional, Type

import html2text
import requests
from crewai_tools import RagTool
from pydantic import BaseModel, Field
from sec_api import QueryApi


def _rag_config() -> dict:
    # Use /tmp-compatible storage for serverless environments like Vercel.
    return {
        "embedding_model": {"provider": "onnx"},
        "vectordb": {
            "provider": "chromadb",
            "config": {"dir": os.getenv("RAG_DB_DIR", "/tmp/stock-analysis-db")},
        },
    }


class FixedSEC10KToolSchema(BaseModel):
    search_query: str = Field(
        ..., description="Mandatory query you would like to search from the 10-K report"
    )


class SEC10KToolSchema(FixedSEC10KToolSchema):
    stock_name: str = Field(
        ..., description="Mandatory valid stock name you would like to search"
    )


class SEC10KTool(RagTool):
    name: str = "Search in the specified 10-K form"
    description: str = (
        "A tool that can be used to semantic search a query from a 10-K form for a specified company."
    )
    args_schema: Type[BaseModel] = SEC10KToolSchema
    collection_name: str = "sec_10k_onnx_collection"
    _max_chars: int = 1200

    def __init__(self, stock_name: Optional[str] = None, **kwargs):
        kwargs.setdefault("config", _rag_config())
        super().__init__(**kwargs)
        if stock_name is not None:
            content = self.get_10k_url_content(stock_name)
            if content:
                self.add(content)
                self.description = (
                    "A tool that can be used to semantic search a query from "
                    f"{stock_name}'s latest 10-K SEC form content."
                )
                self.args_schema = FixedSEC10KToolSchema
                self._generate_description()

    def get_10k_url_content(self, stock_name: str) -> Optional[str]:
        try:
            query_api = QueryApi(api_key=os.environ["SEC_API_API_KEY"])
            query = {
                "query": {
                    "query_string": {
                        "query": f'ticker:{stock_name} AND formType:"10-K"'
                    }
                },
                "from": "0",
                "size": "1",
                "sort": [{"filedAt": {"order": "desc"}}],
            }
            filings = query_api.get_filings(query)["filings"]
            if len(filings) == 0:
                print("No filings found for this stock.")
                return None

            url = filings[0]["linkToFilingDetails"]
            headers = {
                "User-Agent": "crewai.com bisan@crewai.com",
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov",
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            h = html2text.HTML2Text()
            h.ignore_links = False
            text = h.handle(response.content.decode("utf-8"))
            text = re.sub(r"[^a-zA-Z$0-9\s\n]", "", text)
            return text
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            print(f"Error fetching 10-K URL: {e}")
            return None

    def add(self, *args: Any, **kwargs: Any) -> None:
        kwargs["data_type"] = "text"
        super().add(*args, **kwargs)

    def _run(
        self, search_query: str, stock_name: Optional[str] = None, **kwargs: Any
    ) -> Any:
        if stock_name:
            content = self.get_10k_url_content(stock_name)
            if content:
                self.add(content)
        kwargs.pop("stock_name", None)
        raw = super()._run(query=search_query, limit=1, **kwargs)
        if isinstance(raw, str) and len(raw) > self._max_chars:
            return raw[: self._max_chars] + "\n\n[truncated]"
        return raw


class FixedSEC10QToolSchema(BaseModel):
    search_query: str = Field(
        ..., description="Mandatory query you would like to search from the 10-Q report"
    )


class SEC10QToolSchema(FixedSEC10QToolSchema):
    stock_name: str = Field(
        ..., description="Mandatory valid stock name you would like to search"
    )


class SEC10QTool(RagTool):
    name: str = "Search in the specified 10-Q form"
    description: str = (
        "A tool that can be used to semantic search a query from a 10-Q form for a specified company."
    )
    args_schema: Type[BaseModel] = SEC10QToolSchema
    collection_name: str = "sec_10q_onnx_collection"
    _max_chars: int = 1200

    def __init__(self, stock_name: Optional[str] = None, **kwargs):
        kwargs.setdefault("config", _rag_config())
        super().__init__(**kwargs)
        if stock_name is not None:
            content = self.get_10q_url_content(stock_name)
            if content:
                self.add(content)
                self.description = (
                    "A tool that can be used to semantic search a query from "
                    f"{stock_name}'s latest 10-Q SEC form content."
                )
                self.args_schema = FixedSEC10QToolSchema
                self._generate_description()

    def get_10q_url_content(self, stock_name: str) -> Optional[str]:
        try:
            query_api = QueryApi(api_key=os.environ["SEC_API_API_KEY"])
            query = {
                "query": {
                    "query_string": {
                        "query": f'ticker:{stock_name} AND formType:"10-Q"'
                    }
                },
                "from": "0",
                "size": "1",
                "sort": [{"filedAt": {"order": "desc"}}],
            }
            filings = query_api.get_filings(query)["filings"]
            if len(filings) == 0:
                print("No filings found for this stock.")
                return None

            url = filings[0]["linkToFilingDetails"]
            headers = {
                "User-Agent": "crewai.com bisan@crewai.com",
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov",
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            h = html2text.HTML2Text()
            h.ignore_links = False
            text = h.handle(response.content.decode("utf-8"))
            text = re.sub(r"[^a-zA-Z$0-9\s\n]", "", text)
            return text
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            print(f"Error fetching 10-Q URL: {e}")
            return None

    def add(self, *args: Any, **kwargs: Any) -> None:
        kwargs["data_type"] = "text"
        super().add(*args, **kwargs)

    def _run(
        self, search_query: str, stock_name: Optional[str] = None, **kwargs: Any
    ) -> Any:
        if stock_name:
            content = self.get_10q_url_content(stock_name)
            if content:
                self.add(content)
        kwargs.pop("stock_name", None)
        raw = super()._run(query=search_query, limit=1, **kwargs)
        if isinstance(raw, str) and len(raw) > self._max_chars:
            return raw[: self._max_chars] + "\n\n[truncated]"
        return raw
