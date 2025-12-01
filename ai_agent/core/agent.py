"""
Main AI Agent implementation
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseAgent, BaseTool, BaseMemory, BaseNLP, Message, AgentResponse, ToolCall
from ..config.settings import settings, agent_config
from ..memory.memory_manager import MemoryManager
from ..nlp.processor import NLPProcessor
from ..tools.tool_manager import ToolManager
from ..utils.logger import setup_logger


class AIAgent(BaseAgent):
    """Main AI Agent implementation with full functionality"""
    
    def __init__(self, name: Optional[str] = None, custom_config: Optional[Dict[str, Any]] = None):
        config = agent_config.settings.dict()
        if custom_config:
            config.update(custom_config)
        
        super().__init__(name or settings.agent_name, config)
        
        # Setup logging
        self.logger = setup_logger(self.name, settings.log_level, settings.log_file)
        
        # Initialize components
        self.memory_manager = MemoryManager(settings.database_url, settings.max_memory_size)
        self.nlp_processor = NLPProcessor(settings.openai_api_key, settings.openai_model)
        self.tool_manager = ToolManager()
        
        # Agent state
        self.is_initialized = False
        self.conversation_context = {}
        
        self.logger.info(f"AI Agent '{self.name}' created with session ID: {self.session_id}")
    
    async def initialize(self):
        """Initialize the agent and its components"""
        if self.is_initialized:
            return
        
        try:
            await self.memory_manager.initialize()
            await self.nlp_processor.initialize()
            await self.tool_manager.initialize()
            
            # Load default tools
            await self._load_default_tools()
            
            self.is_initialized = True
            self.logger.info("AI Agent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Agent: {e}")
            raise
    
    async def _load_default_tools(self):
        """Load default tools based on configuration"""
        from ..tools.web_search import WebSearchTool
        from ..tools.code_executor import CodeExecutorTool
        from ..tools.file_manager import FileManagerTool
        from ..tools.calculator import CalculatorTool
        
        # Add tools based on configuration
        if agent_config.tools_config["web_search"]["enabled"]:
            await self.tool_manager.add_tool(WebSearchTool())
        
        if agent_config.tools_config["code_execution"]["enabled"]:
            await self.tool_manager.add_tool(CodeExecutorTool())
        
        if agent_config.tools_config["file_operations"]["enabled"]:
            await self.tool_manager.add_tool(FileManagerTool())
        
        # Always add calculator
        await self.tool_manager.add_tool(CalculatorTool())
    
    async def process_message(self, message: str, user_id: Optional[str] = None) -> AgentResponse:
        """Process a user message and return a response"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Create user message
            user_message = Message(
                id="",
                role="user",
                content=message,
                timestamp=datetime.now(),
                metadata={"user_id": user_id}
            )
            
            # Store user message in memory
            await self.memory_manager.store_message(user_message)
            
            # Get conversation history
            history = await self.memory_manager.get_conversation_history(limit=20)
            
            # Process input with NLP
            nlp_result = await self.nlp_processor.process_input(message)
            
            # Update conversation context
            self.conversation_context.update(nlp_result)
            
            # Check if tools are needed
            tool_calls = []
            if nlp_result.get("requires_tools"):
                tool_calls = await self._execute_tools(nlp_result.get("tool_requests", []))
            
            # Generate response
            response_content = await self.nlp_processor.generate_response(
                history, 
                self.conversation_context,
                tool_calls
            )
            
            # Create agent response
            agent_response = AgentResponse(
                content=response_content,
                tool_calls=tool_calls,
                metadata={
                    "session_id": self.session_id,
                    "nlp_result": nlp_result,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Store agent response in memory
            assistant_message = Message(
                id="",
                role="assistant",
                content=response_content,
                timestamp=datetime.now(),
                metadata={"tool_calls": [tc.to_dict() for tc in tool_calls]}
            )
            await self.memory_manager.store_message(assistant_message)
            
            self.logger.info(f"Processed message from user {user_id}: {message[:100]}...")
            return agent_response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            error_response = AgentResponse(
                content=f"I apologize, but I encountered an error while processing your message: {str(e)}",
                metadata={"error": str(e)}
            )
            return error_response
    
    async def _execute_tools(self, tool_requests: List[Dict[str, Any]]) -> List[ToolCall]:
        """Execute requested tools"""
        tool_calls = []
        
        for request in tool_requests:
            tool_name = request.get("name")
            parameters = request.get("parameters", {})
            
            try:
                result = await self.tool_manager.execute_tool(tool_name, parameters)
                tool_call = ToolCall(
                    id="",
                    name=tool_name,
                    parameters=parameters,
                    result=result
                )
                tool_calls.append(tool_call)
                
            except Exception as e:
                self.logger.error(f"Error executing tool {tool_name}: {e}")
                tool_call = ToolCall(
                    id="",
                    name=tool_name,
                    parameters=parameters,
                    error=str(e)
                )
                tool_calls.append(tool_call)
        
        return tool_calls
    
    async def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to the agent's toolkit"""
        await self.tool_manager.add_tool(tool)
        self.logger.info(f"Added tool: {tool.name}")
    
    async def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent's toolkit"""
        await self.tool_manager.remove_tool(tool_name)
        self.logger.info(f"Removed tool: {tool_name}")
    
    async def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return await self.tool_manager.get_available_tools()
    
    async def reset_session(self) -> None:
        """Reset the agent's session and memory"""
        await self.memory_manager.clear_memory()
        self.conversation_context = {}
        self.session_id = str(uuid.uuid4())
        self.logger.info("Agent session reset")
    
    async def get_conversation_history(self, limit: Optional[int] = None) -> List[Message]:
        """Get conversation history"""
        return await self.memory_manager.get_conversation_history(limit)
    
    async def search_memory(self, query: str, limit: int = 10) -> List[Message]:
        """Search memory for relevant messages"""
        return await self.memory_manager.search_memory(query, limit)
    
    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics and status"""
        history = await self.memory_manager.get_conversation_history()
        tools = await self.get_available_tools()
        
        return {
            "name": self.name,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "is_initialized": self.is_initialized,
            "message_count": len(history),
            "available_tools": tools,
            "conversation_context_size": len(self.conversation_context),
            "uptime": (datetime.now() - self.created_at).total_seconds()
        }
    
    async def shutdown(self):
        """Gracefully shutdown the agent"""
        try:
            await self.memory_manager.close()
            self.logger.info("AI Agent shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Convenience function to create and initialize an agent
async def create_agent(name: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> AIAgent:
    """Create and initialize an AI agent"""
    agent = AIAgent(name, config)
    await agent.initialize()
    return agent