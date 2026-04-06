import os
from typing import Dict, Any
from .tool_interface import MedicalTool
from ..tavily_client import TavilyClient
from src.telemetry.logger import logger


class SymptomSearchingTool(MedicalTool):
    """Công cụ tìm kiếm thông tin triệu chứng bằng Tavily."""

    def __init__(self):
        super().__init__(
            name="symptom_searching",
            description="Tìm kiếm thông tin chi tiết về triệu chứng bệnh dựa trên truy vấn của người dùng."
        )
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None

    def execute(self, query: str) -> Dict[str, Any]:
        """
        Thực thi công cụ tìm kiếm triệu chứng bệnh.

        Args:
            query: Mô tả hoặc tên triệu chứng.

        Returns:
            Kết quả tìm kiếm theo định dạng chung.
        """
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
            enhanced_query = f"triệu chứng bệnh {query} nguyên nhân điều trị"
            response = self.client.search(
                query=enhanced_query,
                max_results=10,
                include_answer=True
            )

            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")
                })

            logger.info(f"Symptom search: '{query}' -> {len(results)} results")
            return {
                "status": "success",
                "tool": self.name,
                "query": query,
                "data": results,
                "message": f"Tìm thấy {len(results)} kết quả liên quan đến triệu chứng.",
                "answer": response.get("answer", "")
            }
        except Exception as exc:
            logger.error(f"Symptom search failed: {exc}")
            return {
                "status": "error",
                "tool": self.name,
                "query": query,
                "data": [],
                "message": f"Lỗi khi tìm kiếm triệu chứng: {exc}"
            }
