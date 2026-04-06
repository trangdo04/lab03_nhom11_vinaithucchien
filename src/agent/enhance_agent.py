"""Enhanced medical agent with LangGraph flow and node-based reasoning.

Flow:
User Input -> User Analysis Node -> [General Mode or Observation Node]
Observation Node -> Tool Searching -> Observation results
Observation Node -> [Predict Node or Re-question Node]
"""

import importlib.util
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

# Ensure the repository root is on sys.path so src imports work when running this script directly.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import Config
from src.core.llm_provider import LLMProvider
from src.agent.tools import MedicalTool
from src.telemetry.logger import logger

langgraph = None
LANGGRAPH_AVAILABLE = False
if importlib.util.find_spec("langgraph") is not None:
    try:
        langgraph = importlib.import_module("langgraph")
        LANGGRAPH_AVAILABLE = True
    except Exception:
        LANGGRAPH_AVAILABLE = False


class EnhancedAgent:
    """Enhanced medical agent with node-based reasoning."""

    def __init__(
        self,
        llm: LLMProvider,
        tools: List[MedicalTool],
        max_steps: int = 5
    ):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps
        self.user_history: List[str] = []
        self.observations: List[str] = []
        self.requested_more_info = False
        self._build_flow_graph()

    def _build_flow_graph(self) -> None:
        self.flow_definition = {
            "User Analysis": ["General Mode", "Observation"],
            "Observation": ["Predict", "Re-question"],
            "General Mode": [],
            "Predict": [],
            "Re-question": ["Observation"]
        }
        self.graph = self._create_langgraph() if LANGGRAPH_AVAILABLE else None

    def _create_langgraph(self) -> Optional[Any]:
        try:
            graph_class = getattr(langgraph, "Graph", None)
            node_class = getattr(langgraph, "Node", None)
            if not graph_class or not node_class:
                return None
            graph = graph_class()
            for node_name in self.flow_definition:
                graph.add_node(node_class(name=node_name))
            for source, targets in self.flow_definition.items():
                for target in targets:
                    graph.add_edge(source, target)
            return graph
        except Exception:
            return None

    def _parse_json_flag(self, content: str, key: str) -> Optional[Any]:
        json_value = self._try_parse_json(content, key)
        if json_value is not None:
            return json_value
        return self._try_parse_simple_flag(content, key)

    def _try_parse_json(self, content: str, key: str) -> Optional[Any]:
        try:
            decoded = json.loads(content)
            if isinstance(decoded, dict):
                return decoded.get(key)
        except Exception:
            return None
        return None

    def _try_parse_simple_flag(self, content: str, key: str) -> Optional[Any]:
        pattern = rf'"{key}"\s*:\s*(true|false|\".*?\"|\d+)'
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            return None
        raw = match.group(1).strip()
        if raw.lower() == "true":
            return True
        if raw.lower() == "false":
            return False
        if raw.startswith('"') and raw.endswith('"'):
            return raw[1:-1]
        if raw.isdigit():
            return int(raw)
        return None

    def _classify_medical_question(self, user_input: str) -> bool:
        prompt = (
            "Bạn là một bộ phân loại câu hỏi y tế. Trả lời dưới dạng JSON gồm:\n"
            "{\"medical\": true/false, \"reason\": \"...\"}.\n"
            f"Câu hỏi của người dùng: {user_input}\n"
            "Chỉ cung cấp JSON hợp lệ."
        )
        response = self.llm.generate(prompt=prompt)
        content = response.get("content", "")
        medical_flag = self._parse_json_flag(content, "medical")
        if isinstance(medical_flag, bool):
            return medical_flag
        return self._keyword_medical_check(user_input)

    def _keyword_medical_check(self, user_input: str) -> bool:
        medical_terms = [
            "triệu chứng", "sốt", "ho", "đau", "nhức", "buồn nôn",
            "nôn", "phát ban", "nhiễm trùng", "điều trị", "thuốc", "dược",
            "chẩn đoán", "bác sĩ", "sức khỏe", "bệnh", "virus", "vi khuẩn"
        ]
        lowered = user_input.lower()
        return any(term in lowered for term in medical_terms)

    def _general_mode(self, user_input: str) -> str:
        if "general_searching" in self.tools:
            result = self.tools["general_searching"].execute(user_input)
            if result.get("status") == "success" and result.get("data"):
                return self._format_tool_response(result)
        prompt = (
            "Bạn là trợ lý chung. Hãy trả lời câu hỏi này rõ ràng và ngắn gọn.\n"
            f"Câu hỏi của người dùng: {user_input}"
        )
        response = self.llm.generate(prompt=prompt)
        return response.get("content", "Xin lỗi, tôi không thể trả lời câu hỏi này.")

    def _search_observations(self, user_input: str) -> List[str]:
        collected: List[str] = []
        for tool_name in ["symptom_searching", "medicine_searching", "general_searching"]:
            if tool_name in self.tools:
                result = self.tools[tool_name].execute(user_input)
                if result.get("status") == "success":
                    collected.append(self._format_tool_response(result))
                else:
                    collected.append(f"{tool_name}: {result.get('message', 'tool error')}")
        return collected

    def _format_tool_response(self, result: Dict[str, Any]) -> str:
        data = result.get("data")
        if isinstance(data, (list, dict)):
            try:
                data = json.dumps(data, ensure_ascii=False)
            except Exception:
                data = str(data)
        return f"{result.get('tool')}: {data or result.get('message', '')}"

    def _has_sufficient_information(self, user_input: str, observations: List[str]) -> bool:
        prompt = (
            "Bạn là trợ lý y tế. Hãy xác định xem thông tin hiện có có đủ để đưa ra gợi ý y tế thận trọng hay không.\n"
            "Chỉ trả lời YES hoặc NO.\n"
            f"Câu hỏi của người dùng: {user_input}\n"
            f"Các quan sát:\n{chr(10).join(observations)}\n"
            "Có đủ thông tin để đưa ra gợi ý y tế không?"
        )
        response = self.llm.generate(prompt=prompt)
        content = response.get("content", "").strip().lower()
        if "yes" in content or "có" in content:
            return True
        if "no" in content or "không" in content:
            return False
        return len(observations) >= 2

    def _predict_node(self, user_input: str, observations: List[str]) -> str:
        prompt = (
            "Bạn là trợ lý y tế. Dùng câu hỏi và các quan sát sau để cung cấp câu trả lời cẩn trọng và an toàn. "
            "Hãy rõ ràng rằng đây không phải là tư vấn y tế chính thức và khuyến nghị tham khảo chuyên gia nếu cần.\n\n"
            f"Câu hỏi của người dùng: {user_input}\n"
            f"Các quan sát:\n{chr(10).join(observations)}\n"
            "Trả lời ngắn gọn, thân thiện và đúng mực."
        )
        response = self.llm.generate(prompt=prompt)
        return response.get("content", "Tôi không thể xác định được thông tin vào lúc này.")

    def _requestion_node(self, user_input: str, observations: List[str]) -> str:
        prompt = (
            "Bạn là trợ lý y tế, cần hỏi lại để làm rõ thông tin. "
            "Người dùng đã hỏi câu hỏi y tế nhưng cần thêm chi tiết.\n"
            f"Câu hỏi của người dùng: {user_input}\n"
            f"Các quan sát:\n{chr(10).join(observations)}\n"
            "Hãy đưa ra một câu hỏi follow-up ngắn gọn để thu thập triệu chứng, thời gian, mức độ nghiêm trọng hoặc bối cảnh."
        )
        response = self.llm.generate(prompt=prompt)
        content = response.get("content", "Vui lòng cho tôi biết thêm về tình trạng của bạn.")
        return content.strip()

    def run(self, user_input: str) -> str:
        logger.log_event("ENHANCED_AGENT_START", {"input": user_input[:120]})
        self.user_history.append(user_input)

        if not self._classify_medical_question(user_input):
            logger.log_event("ENHANCED_AGENT_GENERAL_MODE", {})
            return self._general_mode(user_input)

        self.observations = self._search_observations(user_input)
        if self._has_sufficient_information(user_input, self.observations):
            answer = self._predict_node(user_input, self.observations)
            logger.log_event("ENHANCED_AGENT_PREDICT", {})
            return answer

        self.requested_more_info = True
        follow_up = self._requestion_node(user_input, self.observations)
        logger.log_event("ENHANCED_AGENT_REQUESTION", {})
        return follow_up


def main() -> None:
    llm = Config.get_llm_provider()
    tools = Config.get_tools()
    agent = EnhancedAgent(llm=llm, tools=tools, max_steps=Config.MAX_AGENT_STEPS)

    print("Agent y tế nâng cao")
    print("Gõ 'quit' để thoát. Gõ 'history' để xem lịch sử câu hỏi gần đây.\n")

    while True:
        user_input = input("Bạn: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break
        if user_input.lower() == "history":
            for idx, text in enumerate(agent.user_history[-10:], start=1):
                print(f"{idx}. {text}")
            continue

        answer = agent.run(user_input)
        print(f"Agent: {answer}\n")


if __name__ == "__main__":
    main()
