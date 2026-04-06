import os
from typing import Dict, Any, List
from .tool_interface import MedicalTool
from tavily import TavilyClient

class GeneralSearchingTool(MedicalTool):
    """Tool for performing general medical searches."""

    def __init__(self):
        super().__init__(
            name="general_searching",
            description="Search general medical information, conditions, treatments, and health topics."

        )
        self.client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    def execute(self, query: str) -> Dict[str, Any]:

        try:
            search_query = f"medical symptoms diseases treatment: {query}"

            response = self.client.search(
                query=search_query,
                search_depth="advanced",
                max_results=5
            )

            results = response.get("results", [])

            if not results:
                return {
                    "status": "success",
                    "tool": self.name,
                    "query": query,
                    "data": [],
                    "message": "No relevant medical information found."
                }

            extracted: List[Dict[str, str]] = []
            for r in results:
                extracted.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("content", ""),
                    "url": r.get("url", "")
                })

            return {
                "status": "success",
                "tool": self.name,
                "query": query,
                "data": extracted,
                "message": f"Found {len(extracted)} medical search results."
            }

        except Exception as e:
            return {
                "status": "error",
                "tool": self.name,
                "query": query,
                "data": [],
                "message": f"Medical search failed: {str(e)}"
            }
