"""
Unit tests for the ReAct Agent.
"""

import unittest
import json
import os
import tempfile
from unittest.mock import Mock, MagicMock, patch

from src.agent.agent import ReActAgent
from src.agent.tools import (
    SymptomSearchingTool,
    MedicineSearchingTool,
    GeneralSearchingTool
)


class TestReActAgent(unittest.TestCase):
    """Test ReAct Agent functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.mock_llm.model_name = "test-model"
        
        self.tools = [
            SymptomSearchingTool(),
            MedicineSearchingTool(),
            GeneralSearchingTool()
        ]
        
        # Create temporary history file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        self.agent = ReActAgent(
            llm=self.mock_llm,
            tools=self.tools,
            max_steps=5,
            history_file=self.temp_file.name
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_agent_initialization(self):
        """Test agent initializes with correct parameters."""
        self.assertEqual(self.agent.llm, self.mock_llm)
        self.assertEqual(self.agent.max_steps, 5)
        self.assertEqual(len(self.agent.tools), 3)
        self.assertIn("symptom_searching", self.agent.tools)
        self.assertIn("medicine_searching", self.agent.tools)
        self.assertIn("general_searching", self.agent.tools)
    
    def test_parse_action(self):
        """Test action parsing from LLM response."""
        # Valid action
        text = "Action: symptom_searching(headache and fever)"
        action = self.agent._parse_action(text)
        self.assertIsNotNone(action)
        self.assertEqual(action["tool_name"], "symptom_searching")
        self.assertEqual(action["argument"], "headache and fever")
        
        # Case insensitive
        text_upper = "ACTION: medicine_searching(aspirin)"
        action_upper = self.agent._parse_action(text_upper)
        self.assertIsNotNone(action_upper)
        self.assertEqual(action_upper["tool_name"], "medicine_searching")
        
        # With spaces
        text_spaces = "Action:  general_searching ( fever treatment )"
        action_spaces = self.agent._parse_action(text_spaces)
        self.assertIsNotNone(action_spaces)
        self.assertEqual(action_spaces["argument"], "fever treatment")
        
        # No action
        text_no_action = "This is plain text without action"
        action_none = self.agent._parse_action(text_no_action)
        self.assertIsNone(action_none)
    
    def test_extract_final_answer(self):
        """Test final answer extraction."""
        # Valid final answer
        text = "Final Answer: You should consult a doctor if symptoms persist."
        answer = self.agent._extract_final_answer(text)
        self.assertEqual(answer, "You should consult a doctor if symptoms persist.")
        
        # Case insensitive
        text_lower = "final answer: rest and hydration"
        answer_lower = self.agent._extract_final_answer(text_lower)
        self.assertEqual(answer_lower, "rest and hydration")
        
        # With multiple lines after
        text_multiline = """Final Answer: Based on your symptoms:
1. Possible flu
2. Common cold
Rest well"""
        answer_multiline = self.agent._extract_final_answer(text_multiline)
        self.assertIsNotNone(answer_multiline)
        self.assertIn("Possible flu", answer_multiline)
        
        # No final answer
        text_no_answer = "Some response without final answer"
        answer_none = self.agent._extract_final_answer(text_no_answer)
        self.assertIsNone(answer_none)
    
    def test_execute_tool_success(self):
        """Test successful tool execution."""
        result = self.agent._execute_tool("symptom_searching", "headache")
        self.assertIn("symptom_searching", result)
        self.assertIn("result:", result.lower() or result)
    
    def test_execute_tool_not_found(self):
        """Test tool not found error."""
        result = self.agent._execute_tool("nonexistent_tool", "query")
        self.assertIn("not found", result.lower())
        self.assertIn("Available tools:", result)
    
    def test_get_system_prompt(self):
        """Test system prompt generation."""
        prompt = self.agent.get_system_prompt()
        self.assertIn("ReAct", prompt)
        self.assertIn("Thought:", prompt)
        self.assertIn("Action:", prompt)
        self.assertIn("Observation:", prompt)
        self.assertIn("Final Answer:", prompt)
        self.assertIn("symptom_searching", prompt)
        self.assertIn("medicine_searching", prompt)
        self.assertIn("general_searching", prompt)
    
    def test_conversation_history(self):
        """Test conversation history management."""
        # Initially empty
        history = self.agent.get_conversation_history()
        self.assertEqual(len(history), 0)
        
        # Add messages
        self.agent.history.add_message("user", "Hello")
        self.agent.history.add_message("assistant", "Hi there")
        
        # Check history
        history = self.agent.get_conversation_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")
    
    def test_clear_history(self):
        """Test clearing conversation history."""
        self.agent.history.add_message("user", "Test")
        self.assertEqual(len(self.agent.get_conversation_history()), 1)
        
        self.agent.clear_history()
        self.assertEqual(len(self.agent.get_conversation_history()), 0)
    
    def test_run_with_final_answer(self):
        """Test agent run with final answer in first response."""
        # Mock LLM to return final answer immediately
        self.mock_llm.generate.return_value = {
            "content": "Final Answer: You should rest and stay hydrated."
        }
        
        result = self.agent.run("I'm sick")
        self.assertEqual(result, "You should rest and stay hydrated.")
        
        # Check history
        history = self.agent.get_conversation_history()
        self.assertEqual(len(history), 2)  # user + assistant
    
    def test_run_with_tool_usage(self):
        """Test agent run with tool execution."""
        responses = [
            {"content": "Let me search for information.\nAction: symptom_searching(fever)"},
            {"content": "Final Answer: Based on the search, fever could be from several conditions."}
        ]
        self.mock_llm.generate.side_effect = responses
        
        result = self.agent.run("What causes fever?")
        self.assertIn("fever", result.lower())
        self.assertEqual(len(self.agent.get_conversation_history()), 2)
    
    def test_tool_dict_conversion(self):
        """Test tool metadata conversion."""
        tool = SymptomSearchingTool()
        metadata = tool.to_dict()
        
        self.assertEqual(metadata["name"], "symptom_searching")
        self.assertIn("description", metadata)
        self.assertIsInstance(metadata["description"], str)


class TestSystemPrompt(unittest.TestCase):
    """Test system prompt generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.tools = [
            SymptomSearchingTool(),
            MedicineSearchingTool(),
            GeneralSearchingTool()
        ]
        self.agent = ReActAgent(
            llm=self.mock_llm,
            tools=self.tools
        )
    
    def test_prompt_includes_tools(self):
        """Test that system prompt includes all tools."""
        prompt = self.agent.get_system_prompt()
        
        for tool in self.tools:
            self.assertIn(tool.name, prompt)
            self.assertIn(tool.description, prompt)
    
    def test_prompt_includes_format(self):
        """Test that system prompt includes ReAct format instructions."""
        prompt = self.agent.get_system_prompt()
        
        required_keywords = ["Thought:", "Action:", "Observation:", "Final Answer:"]
        for keyword in required_keywords:
            self.assertIn(keyword, prompt)
    
    def test_prompt_includes_medical_context(self):
        """Test that system prompt includes medical guidance."""
        prompt = self.agent.get_system_prompt()
        
        # Should include disclaimers and safety guidance
        self.assertTrue(
            "medical" in prompt.lower() or 
            "healthcare" in prompt.lower() or
            "consult" in prompt.lower()
        )


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
