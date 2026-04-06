from typing import Dict, Any
import os
from .tool_interface import MedicalTool
from ..tavily_client import TavilyClient
from src.telemetry.logger import logger


class MedicineSearchingTool(MedicalTool):
    """Công cụ tìm kiếm thông tin thuốc và dược phẩm."""

    def __init__(self):
        super().__init__(
            name="medicine_searching",
            description="Tìm kiếm thông tin về thuốc, liều dùng, tác dụng phụ và chỉ định."
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

            search_query = f"thông tin thuốc {normalized_query} công dụng liều dùng tác dụng phụ"

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

            logger.info(f"Medicine search: '{normalized_query}' -> {len(formatted_results)} results")
            return {
                "status": "success",
                "tool": self.name,
                "query": normalized_query,
                "data": formatted_results,
                "message": f"Tìm thấy {len(formatted_results)} kết quả về thuốc."
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
            logger.error(f"Medicine search failed: {e}")
            return {
                "status": "error",
                "tool": self.name,
                "query": (query or "").strip(),
                "data": [],
                "message": f"Lỗi khi tìm kiếm thông tin thuốc: {e}"
            }