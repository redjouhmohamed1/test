"""
Web API routes for the AI Agent
"""

import asyncio
import json
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.agent import AIAgent
from ..core.base import Message
from ..utils.logger import setup_logger

# Setup logging
logger = setup_logger("web_api")

# Create router
router = APIRouter()

# Global agent instance
agent = None

class ChatMessage(BaseModel):
    message: str
    session_id: str = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tools_used: List[str] = []

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.on_event("startup")
async def startup_event():
    """Initialize the AI agent on startup"""
    global agent
    try:
        agent = AIAgent("AI Assistant")
        await agent.initialize()
        logger.info("AI Agent initialized successfully for web API")
    except Exception as e:
        logger.error(f"Failed to initialize AI Agent: {e}")
        raise

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """Handle chat messages via REST API"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=500, detail="AI Agent not initialized")
    
    try:
        # Process the message
        agent_response = await agent.process_message(chat_message.message)
        
        # Extract the content from the agent response
        response_content = agent_response.content if hasattr(agent_response, 'content') else str(agent_response)
        
        # Get the session ID
        session_id = chat_message.session_id or agent.session_id
        
        # Get tools used from the agent response
        tools_used = []
        if hasattr(agent_response, 'tool_calls') and agent_response.tool_calls:
            tools_used = [tool_call.name for tool_call in agent_response.tool_calls]
        
        return ChatResponse(
            response=response_content,
            session_id=session_id,
            tools_used=tools_used
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time chat"""
    global agent
    
    await manager.connect(websocket)
    
    if not agent:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "AI Agent not initialized"
        }))
        return
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "message",
            "content": "Hello! I'm your AI assistant. How can I help you today?",
            "session_id": agent.session_id
        }))
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                user_message = message_data.get("content", "")
                
                # Process the message
                agent_response = await agent.process_message(user_message)
                
                # Extract the content from the agent response
                response_content = agent_response.content if hasattr(agent_response, 'content') else str(agent_response)
                
                # Send response back to client
                await websocket.send_text(json.dumps({
                    "type": "message",
                    "content": response_content,
                    "session_id": agent.session_id
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Error: {str(e)}"
        }))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    global agent
    
    status = "healthy" if agent else "unhealthy"
    
    return JSONResponse({
        "status": status,
        "agent_initialized": agent is not None,
        "session_id": agent.session_id if agent else None
    })

@router.get("/agent/info")
async def agent_info():
    """Get information about the AI agent"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=500, detail="AI Agent not initialized")
    
    return JSONResponse({
        "name": agent.name,
        "session_id": agent.session_id,
        "tools_available": list(agent.tool_manager.tools.keys()) if agent.tool_manager else [],
        "memory_enabled": agent.memory_manager is not None
    })

@router.post("/agent/reset")
async def reset_agent():
    """Reset the AI agent session"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=500, detail="AI Agent not initialized")
    
    try:
        # Create a new agent instance
        agent = AIAgent("AI Assistant")
        await agent.initialize()
        
        return JSONResponse({
            "message": "Agent reset successfully",
            "session_id": agent.session_id
        })
        
    except Exception as e:
        logger.error(f"Error resetting agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting agent: {str(e)}")

@router.get("/conversation/history")
async def get_conversation_history():
    """Get conversation history"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=500, detail="AI Agent not initialized")
    
    try:
        # Get recent messages from memory
        if agent.memory_manager:
            messages = await agent.memory_manager.get_recent_messages(limit=50)
            return JSONResponse({
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                    }
                    for msg in messages
                ]
            })
        else:
            return JSONResponse({"messages": []})
            
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")