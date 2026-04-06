import json
import os
from typing import List, Dict, Any
from datetime import datetime


class ConversationHistory:
    """Manage conversation history using a JSON file."""

    def __init__(self, history_file: str = "conversation_history.json"):
        self.history_file = history_file
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def add_message(self, role: str, content: str, tool_used: str = None) -> None:
        message: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content
        }
        if tool_used:
            message["tool_used"] = tool_used
        self.history.append(message)
        self._save_history()

    def get_context(self) -> str:
        if not self.history:
            return "No previous conversation history."
        parts = ["Previous conversation history:"]
        for msg in self.history[-10:]:
            entry = f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
            if "tool_used" in msg:
                entry += f" [Tool: {msg['tool_used']}]"
            parts.append(entry)
        return "\n".join(parts)

    def _save_history(self) -> None:
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def clear_history(self) -> None:
        self.history = []
        self._save_history()

    def get_full_history(self) -> List[Dict[str, Any]]:
        return list(self.history)
