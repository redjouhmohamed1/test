"""
Base classes and interfaces for the AI Agent system
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class Message:
    """Represents a message in a conversation"""
    id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now()


@dataclass
class ToolCall:
    """Represents a tool call made by the agent"""
    id: str
    name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now()
    
    def to_dict(self):
        """Convert to dictionary with serializable values"""
        return {
            'id': self.id,
            'name': self.name,
            'parameters': self.parameters,
            'result': self.result,
            'error': self.error,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class AgentResponse:
    """Represents a response from the agent"""
    content: str
    tool_calls: List[ToolCall] = None
    metadata: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    
    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []
    
    def to_dict(self):
        """Convert to dictionary with serializable values"""
        return {
            'content': self.content,
            'tool_calls': [tc.to_dict() for tc in self.tool_calls] if self.tool_calls else [],
            'metadata': self.metadata,
            'confidence': self.confidence
        }


class BaseMemory(ABC):
    """Abstract base class for memory systems"""
    
    @abstractmethod
    async def store_message(self, message: Message) -> None:
        """Store a message in memory"""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, limit: Optional[int] = None) -> List[Message]:
        """Retrieve conversation history"""
        pass
    
    @abstractmethod
    async def clear_memory(self) -> None:
        """Clear all stored memory"""
        pass
    
    @abstractmethod
    async def search_memory(self, query: str, limit: int = 10) -> List[Message]:
        """Search memory for relevant messages"""
        pass


class BaseTool(ABC):
    """Abstract base class for agent tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tool with given parameters"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters"""
        pass


class BaseNLP(ABC):
    """Abstract base class for NLP processors"""
    
    @abstractmethod
    async def process_input(self, text: str) -> Dict[str, Any]:
        """Process input text and extract relevant information"""
        pass
    
    @abstractmethod
    async def generate_response(self, messages: List[Message], context: Dict[str, Any]) -> str:
        """Generate a response based on messages and context"""
        pass
    
    @abstractmethod
    async def extract_intent(self, text: str) -> Dict[str, Any]:
        """Extract intent from user input"""
        pass


class BaseAgent(ABC):
    """Abstract base class for AI agents"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.now()
    
    @abstractmethod
    async def process_message(self, message: str, user_id: Optional[str] = None) -> AgentResponse:
        """Process a user message and return a response"""
        pass
    
    @abstractmethod
    async def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to the agent's toolkit"""
        pass
    
    @abstractmethod
    async def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent's toolkit"""
        pass
    
    @abstractmethod
    async def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        pass
    
    @abstractmethod
    async def reset_session(self) -> None:
        """Reset the agent's session and memory"""
        pass