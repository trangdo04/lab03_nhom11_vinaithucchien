from typing import Dict, Any
from venv import logger
from .tool_interface import MedicalTool
from tavily import TavilyClient
from src.config import Config


class SymptomSearchingTool(MedicalTool):
    """Tool for searching medical symptom information using Tavily API."""

    def __init__(self):
        super().__init__(
            name="symptom_searching",
            description="Tìm kiếm thông tin chi tiết về các triệu chứng bệnh dựa trên yêu cầu của người dùng."
        )
        # Initialize Tavily client with API key from config
        self.tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY)

    def execute(self, query: str) -> Dict[str, Any]:
        """
        Thực thi công cụ tìm kiếm triệu chứng bệnh sử dụng Tavily API.

        Args:
            query: Mô tả hoặc tên triệu chứng bệnh.

        Returns:
            Dict chứa kết quả thực thi công cụ với các thông tin tìm kiếm được.
        """
        try:
            # Nâng cao query để tập trung vào thông tin y tế/triệu chứng
            enhanced_query = f"triệu chứng bệnh {query} nguyên nhân cách điều trị"
            
            # Call Tavily API to search for symptom information
            response = self.tavily_client.search(
                query=enhanced_query,
                max_results=10,
                include_answer=True
            )
            
            # Extract and format search results
            results = []
            if response.get("results"):
                for result in response["results"]:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", "")
                    })
            
            logger.info(f"Symptom search for query '{query}' returned {len(results)} results.")
            return {
                "status": "success",
                "tool": self.name,
                "query": query,
                "data": results,
                "answer": response.get("answer", ""),
                "message": f"Tìm thấy {len(results)} kết quả liên quan đến triệu chứng: {query}"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "tool": self.name,
                "query": query,
                "data": [],
                "error": str(e),
                "message": f"Lỗi khi tìm kiếm thông tin triệu chứng: {str(e)}"
            }
