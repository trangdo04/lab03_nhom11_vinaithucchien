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
            response = self.client.query(enhanced_query)

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
            extracted = []
            for item in results:
                if isinstance(item, dict):
                    extracted.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", "")
                    })
                else:
                    extracted.append({"title": "Kết quả triệu chứng", "url": "", "content": str(item)})

            logger.info(f"Symptom search: '{query}' -> {len(extracted)} results")
            return {
                "status": "success",
                "tool": self.name,
                "query": query,
                "data": extracted,
                "message": f"Tìm thấy {len(extracted)} kết quả liên quan đến triệu chứng.",
                "answer": response.get("data", "")
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
