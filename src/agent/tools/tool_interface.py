from abc import ABC, abstractmethod
from typing import Dict, Any


class MedicalTool(ABC):
    """Base interface for medical tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, query: str) -> Dict[str, Any]:
        """
        Execute the tool using the provided query.

        Args:
            query: The search query or prompt for the tool.

        Returns:
            A dictionary containing the tool execution result.
        """
        pass

    def to_dict(self) -> Dict[str, str]:
        """Return tool metadata in dictionary form."""
        return {
            "name": self.name,
            "description": self.description
        }
