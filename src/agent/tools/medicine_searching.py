from typing import Dict, Any
import os
from tavily import TavilyClient
from .tool_interface import MedicalTool


class MedicineSearchingTool(MedicalTool):
    """Tool for searching medicine and pharmaceutical information."""

    def __init__(self):
        super().__init__(
            name="medicine_searching",
            description="Search for information about medicines and their uses."
        )
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None

    def execute(self, query: str) -> Dict[str, Any]:
        """
        Execute the medicine searching tool.

        Args:
            query: Medicine name or related question.

        Returns:
            Dict with tool execution result.
        """
        try:
            normalized_query = (query or "").strip()
            if not normalized_query:
                raise ValueError("Query must not be empty.")

            if not self.client:
                raise RuntimeError("TAVILY_API_KEY is not set in environment.")

            search_query = f"medicine {normalized_query} uses dosage side effects"

            response = self.client.search(
                query=search_query,
                search_depth="advanced",
                max_results=5
            )

            results = response.get("results", [])

            formatted_results = [
                {
                    "title": (r.get("title") or "").strip(),
                    "url": (r.get("url") or "").strip(),
                    "content": (r.get("content") or "").strip()[:1000]
                }
                for r in results
            ]

            return {
                "status": "success",
                "tool": self.name,
                "query": normalized_query,
                "data": formatted_results,
                "message": f"Found {len(formatted_results)} results from Tavily"
            }

        except (ValueError, RuntimeError) as e:
            return {
                "status": "error",
                "tool": self.name,
                "query": (query or "").strip(),
                "data": [],
                "message": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "tool": self.name,
                "query": (query or "").strip(),
                "data": [],
                "message": f"Tavily search failed: {e}"
            }