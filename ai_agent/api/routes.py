"""
API routes for the AI Agent
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import logging

from ..core.agent import AIAgent, create_agent
from ..config.settings import settings

# Global agent instance
agent: Optional[AIAgent] = None
logger = logging.getLogger(__name__)

# Pydantic models for API
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    tool_calls: List[Dict[str, Any]] = []
    metadata: Optional[Dict[str, Any]] = None

class AgentStats(BaseModel):
    name: str
    session_id: str
    created_at: str
    is_initialized: bool
    message_count: int
    available_tools: List[str]
    conversation_context_size: int
    uptime: float

# Create router
router = APIRouter()

async def get_agent() -> AIAgent:
    """Get or create the global agent instance"""
    global agent
    if agent is None:
        agent = await create_agent()
    return agent

@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Send a message to the AI agent"""
    try:
        agent_instance = await get_agent()
        response = await agent_instance.process_message(message.message, message.user_id)
        
        return ChatResponse(
            response=response.content,
            tool_calls=[tc.__dict__ for tc in response.tool_calls],
            metadata=response.metadata
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/stats", response_model=AgentStats)
async def get_agent_stats():
    """Get agent statistics"""
    try:
        agent_instance = await get_agent()
        stats = await agent_instance.get_agent_stats()
        return AgentStats(**stats)
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/tools")
async def get_available_tools():
    """Get list of available tools"""
    try:
        agent_instance = await get_agent()
        tools = await agent_instance.get_available_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/history")
async def get_conversation_history(limit: Optional[int] = 20):
    """Get conversation history"""
    try:
        agent_instance = await get_agent()
        history = await agent_instance.get_conversation_history(limit)
        return {
            "history": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in history
            ]
        }
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/reset")
async def reset_agent():
    """Reset the agent session"""
    try:
        agent_instance = await get_agent()
        await agent_instance.reset_session()
        return {"message": "Agent session reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/search")
async def search_memory(query: str, limit: int = 10):
    """Search agent memory"""
    try:
        agent_instance = await get_agent()
        results = await agent_instance.search_memory(query, limit)
        return {
            "query": query,
            "results": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in results
            ]
        }
    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        agent_instance = await get_agent()
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message = message_data.get("message", "")
            user_id = message_data.get("user_id")
            
            if not message:
                await websocket.send_text(json.dumps({
                    "error": "No message provided"
                }))
                continue
            
            # Process message
            response = await agent_instance.process_message(message, user_id)
            
            # Send response
            response_data = {
                "response": response.content,
                "tool_calls": [tc.__dict__ for tc in response.tool_calls],
                "metadata": response.metadata
            }
            
            await websocket.send_text(json.dumps(response_data))
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "error": str(e)
        }))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Agent API"}