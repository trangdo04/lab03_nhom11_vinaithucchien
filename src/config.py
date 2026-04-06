"""
Configuration loader for the medical agent application.
Loads settings from .env file.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # LLM Provider Settings
    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "google")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash-lite")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # Local Model
    LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Agent Settings
    MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", "5"))
    HISTORY_FILE = os.getenv("HISTORY_FILE", "conversation_history.json")
    
    @staticmethod
    def get_llm_provider():
        """Get LLM provider based on configuration."""
        provider = Config.DEFAULT_PROVIDER.lower()
        model = Config.DEFAULT_MODEL
        
        if provider == "openai":
            from src.core.openai_provider import OpenAIProvider
            return OpenAIProvider(model_name=model)
        
        elif provider == "google" or provider == "gemini":
            from src.core.gemini_provider import GeminiProvider
            return GeminiProvider(model_name=model)
        
        elif provider == "local":
            from src.core.local_provider import LocalProvider
            return LocalProvider(model_path=Config.LOCAL_MODEL_PATH)
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @staticmethod
    def get_tools():
        """Get list of available tools."""
        from src.agent.tools import (
            SymptomSearchingTool,
            MedicineSearchingTool,
            GeneralSearchingTool
        )
        
        return [
            SymptomSearchingTool(),
            MedicineSearchingTool(),
            GeneralSearchingTool()
        ]
