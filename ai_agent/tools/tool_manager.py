"""
Tool management system for the AI Agent
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging

from ..core.base import BaseTool


class ToolManager:
    """Manages tools available to the AI agent"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize the tool manager"""
        self.logger.info("Tool manager initialized")
    
    async def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to the manager"""
        self.tools[tool.name] = tool
        self.logger.info(f"Added tool: {tool.name}")
    
    async def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the manager"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.logger.info(f"Removed tool: {tool_name}")
        else:
            self.logger.warning(f"Tool not found: {tool_name}")
    
    async def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a specific tool"""
        return self.tools.get(tool_name)
    
    async def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list(self.tools.keys())
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool with given parameters"""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        try:
            result = await tool.execute(parameters)
            self.logger.info(f"Tool '{tool_name}' executed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error executing tool '{tool_name}': {e}")
            raise
    
    async def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all available tools"""
        schemas = {}
        for name, tool in self.tools.items():
            try:
                schemas[name] = tool.get_schema()
            except Exception as e:
                self.logger.error(f"Error getting schema for tool '{name}': {e}")
                schemas[name] = {"error": str(e)}
        return schemas
    
    async def validate_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate parameters for a specific tool"""
        tool = self.tools.get(tool_name)
        if not tool:
            return False
        
        try:
            schema = tool.get_schema()
            # Basic validation - check required parameters
            required = schema.get("required", [])
            for param in required:
                if param not in parameters:
                    return False
            return True
        except Exception:
            return False