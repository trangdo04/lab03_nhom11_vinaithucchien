"""
Interactive Medical Agent Chatbot Demo
Chat with the medical agent through terminal
"""

import sys
import os
from src.agent.agent import ReActAgent
from src.config import Config


def main():
    """Run interactive chatbot."""
    
    print("\n" + "=" * 60)
    print("   Medical Agent Chatbot")
    print("=" * 60)
    print(f"Provider: {Config.DEFAULT_PROVIDER.upper()}")
    print(f"Model: {Config.DEFAULT_MODEL}")
    print("-" * 60)
    print("Type 'quit' to exit, 'clear' to clear history\n")
    
    try:
        # Initialize agent from config
        llm = Config.get_llm_provider()
        tools = Config.get_tools()
        agent = ReActAgent(llm=llm, tools=tools)
        print("✓ Agent ready\n")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Chat loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                print("Goodbye!")
                break
            
            if user_input.lower() == "clear":
                agent.clear_history()
                print("History cleared.\n")
                continue
            
            # Get agent response
            print("\nExpert: ", end="", flush=True)
            answer = agent.run(user_input)
            print(answer)
            print()
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()
