"""
Configuration management for the AI Agent system
"""

import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-3.5-turbo", env="OPENAI_MODEL")
    
    # Agent Configuration
    agent_name: str = Field("AI Assistant", env="AGENT_NAME")
    agent_personality: str = Field("helpful, friendly, and knowledgeable", env="AGENT_PERSONALITY")
    max_memory_size: int = Field(1000, env="MAX_MEMORY_SIZE")
    conversation_timeout: int = Field(3600, env="CONVERSATION_TIMEOUT")
    
    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(12000, env="PORT")
    debug: bool = Field(True, env="DEBUG")
    
    # Database Configuration
    database_url: str = Field("sqlite:///./agent_memory.db", env="DATABASE_URL")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("agent.log", env="LOG_FILE")
    
    # Tool Configuration
    enable_web_search: bool = Field(True, env="ENABLE_WEB_SEARCH")
    enable_code_execution: bool = Field(True, env="ENABLE_CODE_EXECUTION")
    enable_file_operations: bool = Field(True, env="ENABLE_FILE_OPERATIONS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class AgentConfig:
    """Agent-specific configuration"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.system_prompt = self._build_system_prompt()
        self.tools_config = self._build_tools_config()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent"""
        return f"""You are {self.settings.agent_name}, an AI assistant that is {self.settings.agent_personality}.

Your capabilities include:
- Natural language understanding and generation
- Memory of conversation context
- Tool usage for various tasks
- Problem-solving and analysis
- Code generation and execution
- Web search and information retrieval

Guidelines:
- Be helpful, accurate, and honest
- Ask for clarification when needed
- Use tools when appropriate
- Maintain conversation context
- Provide detailed explanations when requested
- Admit when you don't know something

Remember to be conversational and engaging while maintaining professionalism."""
    
    def _build_tools_config(self) -> Dict[str, Any]:
        """Build configuration for available tools"""
        return {
            "web_search": {
                "enabled": self.settings.enable_web_search,
                "max_results": 5
            },
            "code_execution": {
                "enabled": self.settings.enable_code_execution,
                "timeout": 30,
                "allowed_languages": ["python", "javascript", "bash"]
            },
            "file_operations": {
                "enabled": self.settings.enable_file_operations,
                "allowed_extensions": [".txt", ".py", ".js", ".json", ".csv", ".md"]
            }
        }


# Global settings instance
settings = Settings()
agent_config = AgentConfig(settings)