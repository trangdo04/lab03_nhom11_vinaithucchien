import os
from typing import Any, Dict, Optional

import requests


class TavilyClient:
    """Simple Tavily API client."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = base_url or "https://api.tavily.com/search"

    def query(self, query: str) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "status": "error",
                "tool": "tavily",
                "query": query,
                "data": None,
                "message": "TAVILY_API_KEY is not set in environment variables."
            }

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=30)
            if response.status_code == 401:
                return {
                    "status": "error",
                    "tool": "tavily",
                    "query": query,
                    "data": None,
                    "message": "Tavily authentication failed. Check TAVILY_API_KEY."
                }
            response.raise_for_status()
            result_json = response.json()
        except requests.RequestException as exc:
            return {
                "status": "error",
                "tool": "tavily",
                "query": query,
                "data": None,
                "message": f"Tavily request failed: {str(exc)}"
            }
        except ValueError:
            return {
                "status": "error",
                "tool": "tavily",
                "query": query,
                "data": None,
                "message": "Tavily response could not be parsed as JSON."
            }

        data = self._extract_data(result_json)
        return {
            "status": "success",
            "tool": "tavily",
            "query": query,
            "data": data,
            "message": "Tavily query completed successfully.",
            "raw_response": result_json
        }

    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Backward-compatible alias for query()."""
        return self.query(query)

    def _extract_data(self, result_json: Dict[str, Any]) -> Any:
        if not isinstance(result_json, dict):
            return result_json

        for key in ("results", "answer", "data", "text", "message"):
            if key in result_json:
                return result_json[key]

        return result_json
