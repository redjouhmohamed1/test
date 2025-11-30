"""
AI Agent - A comprehensive AI assistant framework
"""

__version__ = "1.0.0"
__author__ = "AI Agent Team"
__description__ = "A modular AI agent system with natural language processing, memory, and tool integration"

from .core.agent import AIAgent
from .core.base import BaseAgent
from .config.settings import Settings

__all__ = ["AIAgent", "BaseAgent", "Settings"]