import os
from typing import Any, Dict, Optional

import requests


class TavilyClient:
    """Simple Tavily API client."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = base_url or os.getenv("TAVILY_BASE_URL", "https://api.tavily.ai/v1")

    def query(self, query: str) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "status": "error",
                "tool": "tavily",
                "query": query,
                "data": None,
                "message": "TAVILY_API_KEY is not set in environment variables."
            }

        endpoints = ["/query", "/search", "/answer", "/responses"]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"query": query}
        last_error = None

        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=20)
                if response.status_code == 401:
                    return {
                        "status": "error",
                        "tool": "tavily",
                        "query": query,
                        "data": None,
                        "message": "Tavily authentication failed. Check TAVILY_API_KEY."
                    }
                if response.status_code in (404, 405, 400):
                    last_error = f"Endpoint {url} returned {response.status_code}."
                    continue
                response.raise_for_status()
                result_json = response.json()
            except requests.RequestException as exc:
                last_error = str(exc)
                continue
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
                "message": f"Tavily query completed successfully via {endpoint}.",
                "raw_response": result_json,
                "endpoint": endpoint
            }

        return {
            "status": "error",
            "tool": "tavily",
            "query": query,
            "data": None,
            "message": f"Tavily request failed for all endpoints. Last error: {last_error}"
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
