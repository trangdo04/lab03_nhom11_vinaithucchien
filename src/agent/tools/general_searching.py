import os
from typing import Dict, Any, List
from .tool_interface import MedicalTool
from ..tavily_client import TavilyClient
from src.telemetry.logger import logger


class GeneralSearchingTool(MedicalTool):
    """Công cụ tìm kiếm thông tin y tế tổng quát."""

    def __init__(self):
        super().__init__(
            name="general_searching",
            description="Tìm kiếm thông tin y tế tổng quát, điều kiện, điều trị và kiến thức sức khỏe."
        )
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None

    def execute(self, query: str) -> Dict[str, Any]:
        logger.log_event("TOOL_START", {
            "tool": self.name,
            "query_preview": (query or "")[:200]
        })
        if not query or not query.strip():
            return {
                "status": "error",
                "tool": self.name,
                "query": query,
                "data": [],
                "message": "Yêu cầu tìm kiếm không được để trống."
            }

        if not self.client:
            return {
                "status": "error",
                "tool": self.name,
                "query": query,
                "data": [],
                "message": "TAVILY_API_KEY chưa được cấu hình."
            }

        try:
            search_query = f"thông tin y tế chung {query}"
            response = self.client.query(search_query)

            if response.get("status") != "success":
                return {
                    "status": "error",
                    "tool": self.name,
                    "query": query,
                    "data": [],
                    "message": response.get("message", "Lỗi từ Tavily.")
                }

            data = response.get("data", [])
            results = data if isinstance(data, list) else [data]
            if not results or all(not item for item in results):
                return {
                    "status": "success",
                    "tool": self.name,
                    "query": query,
                    "data": [],
                    "message": "Không tìm thấy thông tin phù hợp."
                }

            extracted: List[Dict[str, str]] = []
            for item in results:
                if isinstance(item, dict):
                    extracted.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("content", ""),
                        "url": item.get("url", "")
                    })
                else:
                    extracted.append({"title": "Kết quả tổng hợp", "snippet": str(item), "url": ""})

            logger.info(f"General search: '{query}' -> {len(extracted)} results")
            logger.log_event("TOOL_RESULT", {
                "tool": self.name,
                "status": "success",
                "query": query,
                "result_count": len(extracted)
            })
            return {
                "status": "success",
                "tool": self.name,
                "query": query,
                "data": extracted,
                "message": f"Tìm thấy {len(extracted)} kết quả thông tin y tế."
            }
        except Exception as exc:
            logger.error(f"General search failed: {exc}")
            logger.log_event("TOOL_RESULT", {
                "tool": self.name,
                "status": "error",
                "query": query,
                "message": str(exc)
            })
            return {
                "status": "error",
                "tool": self.name,
                "query": query,
                "data": [],
                "message": f"Lỗi khi tìm kiếm thông tin y tế: {exc}"
            }
