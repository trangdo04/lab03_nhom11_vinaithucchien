import os
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from src.core.llm_provider import LLMProvider
from src.agent.tools import MedicalTool
from src.agent.history_manager import ConversationHistory
from src.telemetry.logger import logger

# Load environment variables from .env file
load_dotenv()


class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Implements full ReAct pattern with tool execution and conversation history.
    """
    
    def __init__(
        self,
        llm: LLMProvider,
        tools: List[MedicalTool],
        max_steps: int = 5,
        history_file: str = "conversation_history.json"
    ):
        """
        Initialize the ReAct Agent.
        
        Args:
            llm: LLMProvider instance (OpenAI, Gemini, Local, etc.)
            tools: List of MedicalTool objects available to the agent
            max_steps: Maximum number of Thought-Action-Observation loops
            history_file: Path to JSON file for conversation history
        """
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps
        self.history = ConversationHistory(history_file)

    def get_system_prompt(self) -> str:
        """
        Get the system prompt that instructs the agent to follow ReAct format.
        Includes:
        1. Available tools and their descriptions
        2. Format instructions: Thought, Action, Observation, Final Answer
        3. Medical context and safety guidelines
        """
        tool_descriptions = "\n".join(
            [f"- {name}: {tool.description}" for name, tool in self.tools.items()]
        )
        
        return f"""You are a medical assistant AI agent. Your goal is to help users with health-related questions.

You have access to the following tools:
{tool_descriptions}

Follow the ReAct format strictly:
1. Thought: Think about what the user is asking and which tools might help
2. Action: Use the tool in this format: Action: tool_name(argument)
3. Observation: Record the results from the tool
4. Repeat Thought/Action/Observation until you have enough information
5. Final Answer: Provide a comprehensive response to the user

Format example:
Thought: The user is asking about symptoms. I should search for this information.
Action: symptom_searching(fever and cough)
Observation: [tool results]
Thought: Now I need more information about treatment options.
Action: general_searching(fever treatment)
Observation: [tool results]
Final Answer: Based on your symptoms...

Important:
- Medical information is for educational purposes only
- Always recommend users consult healthcare professionals for serious concerns
- Be clear about limitations of your knowledge
- Use tools when you need specific information"""

    def _parse_action(self, text: str) -> Optional[Dict[str, str]]:
        """
        Parse Action from LLM response.
        Expected format: Action: tool_name(argument)
        
        Returns:
            Dict with 'tool_name' and 'argument' or None if not found
        """
        pattern = r"Action:\s*(\w+)\s*\((.*?)\)"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            return {
                "tool_name": match.group(1),
                "argument": match.group(2).strip()
            }
        return None

    def _extract_final_answer(self, text: str) -> Optional[str]:
        """
        Extract Final Answer from LLM response.
        Expected format: Final Answer: ...
        
        Returns:
            The final answer text or None if not found
        """
        marker = "final answer:"
        lower_text = text.lower()
        idx = lower_text.find(marker)
        if idx == -1:
            return None

        extracted = text[idx + len(marker):].strip()
        if not extracted:
            return None

        separator = "\n\n"
        end_idx = extracted.find(separator)
        if end_idx != -1:
            extracted = extracted[:end_idx].strip()

        return extracted

    def _execute_tool(self, tool_name: str, argument: str) -> str:
        """
        Execute a tool by name and return the formatted result.
        
        Args:
            tool_name: Name of the tool to execute
            argument: Argument/query to pass to the tool
            
        Returns:
            Formatted observation/result as string
        """
        if tool_name not in self.tools:
            available = ", ".join(self.tools.keys())
            return f"Error: Tool '{tool_name}' not found. Available tools: {available}"
        
        try:
            tool = self.tools[tool_name]
            result = tool.execute(argument)
            
            # Format result for LLM context
            if result.get("status") == "success":
                observation = f"Tool '{tool_name}' result:\n"
                if result.get("data"):
                    observation += str(result["data"])
                else:
                    observation += result.get("message", "No data returned")
            else:
                observation = f"Tool error: {result.get('message', 'Unknown error')}"
            
            return observation
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def run(self, user_input: str) -> str:
        """
        Run the ReAct agent loop.
        
        Process:
        1. Load conversation history and system prompt
        2. Generate LLM response
        3. Parse Thought/Action and execute tools
        4. Append observations and repeat
        5. Extract Final Answer and save to history
        
        Args:
            user_input: The user's question or request
            
        Returns:
            The agent's final answer
        """
        logger.log_event("AGENT_START", {
            "input": user_input[:100] + "..." if len(user_input) > 100 else user_input,
            "model": self.llm.model_name,
            "tools": list(self.tools.keys())
        })
        
        # Add user message to history
        self.history.add_message("user", user_input)
        
        # Get system prompt and history context
        system_prompt = self.get_system_prompt()
        history_context = self.history.get_context()
        
        # Build initial prompt with context
        current_prompt = f"""{history_context}

User: {user_input}

Please help the user with their medical question. Follow the Thought-Action-Observation format carefully."""
        
        step = 0
        final_answer = None
        
        # ReAct loop: Thought-Action-Observation
        while step < self.max_steps and final_answer is None:
            # Generate LLM response
            response = self.llm.generate(
                prompt=current_prompt,
                system_prompt=system_prompt
            )
            
            llm_content = response.get("content", "")
            
            # Try to extract Final Answer
            final_answer = self._extract_final_answer(llm_content)
            
            if final_answer:
                logger.log_event("FINAL_ANSWER_FOUND", {"step": step + 1})
                break
            
            # Try to parse and execute action
            action = self._parse_action(llm_content)
            
            if action:
                tool_name = action["tool_name"]
                argument = action["argument"]
                
                # Execute the tool
                observation = self._execute_tool(tool_name, argument)
                
                # Log tool usage
                logger.log_event("TOOL_EXECUTED", {
                    "tool": tool_name,
                    "step": step + 1,
                    "argument": argument[:50] + "..." if len(argument) > 50 else argument
                })
                
                # Append LLM response and observation to prompt for next iteration
                current_prompt += f"\n\n{llm_content}\n\nObservation: {observation}\n\nThought:"
            else:
                # No action found and no final answer
                if step == self.max_steps - 1:
                    # Last step - use current response as final answer
                    final_answer = llm_content
                else:
                    # Encourage LLM to provide Final Answer
                    current_prompt += f"\n\n{llm_content}\n\nPlease provide your Final Answer:"
            
            step += 1
        
        # Fallback if we didn't get a final answer
        if final_answer is None:
            final_answer = "I encountered an issue generating a response. Please try again or provide more details."
        
        # Do not save assistant responses to history to reduce token usage
        logger.log_event("AGENT_END", {
            "steps": step,
            "answer_length": len(final_answer),
            "has_final_answer": final_answer is not None
        })
        
        return final_answer

    def clear_history(self) -> None:
        """Clear all conversation history."""
        self.history.clear_history()
        logger.log_event("HISTORY_CLEARED", {})
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history."""
        return self.history.get_full_history()
