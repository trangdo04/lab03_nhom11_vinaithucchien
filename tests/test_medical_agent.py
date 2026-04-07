"""
Unit tests for the Medical Agent components.
"""

import unittest
import json
import os
import tempfile
from unittest.mock import Mock, MagicMock

from src.agent.history_manager import ConversationHistory
from src.agent.tools import (
    SymptomSearchingTool,
    MedicineSearchingTool,
    GeneralSearchingTool
)


class TestHistoryManager(unittest.TestCase):
    """Test conversation history management."""
    
    def setUp(self):
        """Create temporary file for testing."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.history = ConversationHistory(self.temp_file.name)
    
    def tearDown(self):
        """Clean up temporary file."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_add_message(self):
        """Test adding messages to history."""
        self.history.add_message("user", "Hello")
        self.assertEqual(len(self.history.get_full_history()), 1)
        
        self.history.add_message("assistant", "Hi there")
        self.assertEqual(len(self.history.get_full_history()), 2)
    
    def test_add_message_with_tool(self):
        """Test adding message with tool information."""
        self.history.add_message("assistant", "Using tool", tool_used="symptom_searching")
        history = self.history.get_full_history()
        self.assertEqual(history[0]["tool_used"], "symptom_searching")
    
    def test_get_context(self):
        """Test getting formatted context."""
        self.history.add_message("user", "What is flu?")
        self.history.add_message("assistant", "Flu is a viral infection")
        
        context = self.history.get_context()
        self.assertIn("USER: What is flu?", context)
        self.assertIn("ASSISTANT: Flu is a viral infection", context)
    
    def test_clear_history(self):
        """Test clearing history."""
        self.history.add_message("user", "Test")
        self.assertEqual(len(self.history.get_full_history()), 1)
        
        self.history.clear_history()
        self.assertEqual(len(self.history.get_full_history()), 0)
    
    def test_persistence(self):
        """Test history is saved and loaded from file."""
        history1 = ConversationHistory(self.temp_file.name)
        history1.add_message("user", "Persistent message")
        
        # Create new instance - should load from file
        history2 = ConversationHistory(self.temp_file.name)
        self.assertEqual(len(history2.get_full_history()), 1)
        self.assertEqual(history2.get_full_history()[0]["content"], "Persistent message")


class TestMedicalTools(unittest.TestCase):
    """Test medical tools."""
    
    def test_symptom_searching_tool(self):
        """Test symptom searching tool initialization and execution."""
        tool = SymptomSearchingTool()
        self.assertEqual(tool.name, "symptom_searching")
        
        result = tool.execute("headache")
        self.assertEqual(result["tool"], "symptom_searching")
        self.assertEqual(result["query"], "headache")
        self.assertEqual(result["status"], "success")
    
    def test_medicine_searching_tool(self):
        """Test medicine searching tool."""
        tool = MedicineSearchingTool()
        self.assertEqual(tool.name, "medicine_searching")
        
        result = tool.execute("aspirin")
        self.assertEqual(result["tool"], "medicine_searching")
        self.assertEqual(result["query"], "aspirin")
        self.assertEqual(result["status"], "success")
    
    def test_general_searching_tool(self):
        """Test general searching tool."""
        tool = GeneralSearchingTool()
        self.assertEqual(tool.name, "general_searching")
        
        result = tool.execute("common cold")
        self.assertEqual(result["tool"], "general_searching")
        self.assertEqual(result["query"], "common cold")
        self.assertEqual(result["status"], "success")
    
    def test_tool_to_dict(self):
        """Test tool metadata conversion."""
        tool = SymptomSearchingTool()
        metadata = tool.to_dict()
        
        self.assertEqual(metadata["name"], "symptom_searching")
        self.assertIn("description", metadata)


class TestMedicalAgent(unittest.TestCase):
    """Test medical agent (requires mock LLM)."""
    
    def setUp(self):
        """Set up mock LLM provider."""
        self.mock_llm = Mock()
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_parse_action(self):
        """Test action parsing from LLM response."""
        from src.agent.agent import ReActAgent
        
        agent = ReActAgent(
            llm=self.mock_llm,
            tools=[SymptomSearchingTool(), MedicineSearchingTool(), GeneralSearchingTool()],
            history_file=self.temp_file.name
        )
        
        # Test valid action
        text = "Action: symptom_searching(headache and fever)"
        action = agent._parse_action(text)
        self.assertIsNotNone(action)
        self.assertEqual(action["tool_name"], "symptom_searching")
        self.assertEqual(action["argument"], "headache and fever")
        
        # Test no action
        text_no_action = "This is plain text"
        action_none = agent._parse_action(text_no_action)
        self.assertIsNone(action_none)
    
    def test_extract_final_answer(self):
        """Test final answer extraction."""
        from src.agent.agent import ReActAgent
        
        agent = ReActAgent(
            llm=self.mock_llm,
            tools=[SymptomSearchingTool(), MedicineSearchingTool(), GeneralSearchingTool()],
            history_file=self.temp_file.name
        )
        
        # Test valid final answer
        text = "Final Answer: You should consult a doctor."
        answer = agent._extract_final_answer(text)
        self.assertEqual(answer, "You should consult a doctor.")
        
        # Test no final answer
        text_no_answer = "Some response without final answer"
        answer_none = agent._extract_final_answer(text_no_answer)
        self.assertIsNone(answer_none)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
