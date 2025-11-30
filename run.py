#!/usr/bin/env python3
"""
Startup script for the AI Agent system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ai_agent.config.settings import settings
from ai_agent.utils.logger import setup_logger

async def initialize_system():
    """Initialize the AI Agent system"""
    logger = setup_logger("ai_agent_startup", settings.log_level)
    
    logger.info("🚀 Starting AI Agent System...")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    
    # Check required directories
    required_dirs = [
        "ai_agent/web/static",
        "ai_agent/web/templates",
        "data"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            logger.info(f"Creating directory: {dir_path}")
            full_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize database directory
    db_dir = project_root / "data"
    if not db_dir.exists():
        db_dir.mkdir(exist_ok=True)
        logger.info("Created database directory")
    
    # Test imports
    try:
        from ai_agent.core.agent import create_agent
        from ai_agent.tools.calculator import CalculatorTool
        from ai_agent.tools.web_search import WebSearchTool
        from ai_agent.tools.file_manager import FileManagerTool
        from ai_agent.memory.memory_manager import MemoryManager
        
        logger.info("✅ All modules imported successfully")
        
        # Test agent creation
        logger.info("🤖 Testing agent initialization...")
        agent = await create_agent()
        stats = await agent.get_agent_stats()
        logger.info(f"Agent '{stats['name']}' initialized successfully")
        logger.info(f"Available tools: {', '.join(stats['available_tools'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ System initialization failed: {e}")
        return False

def main():
    """Main entry point"""
    print("=" * 60)
    print("🤖 AI Agent System")
    print("=" * 60)
    
    # Run initialization
    success = asyncio.run(initialize_system())
    
    if not success:
        print("❌ System initialization failed. Please check the logs.")
        sys.exit(1)
    
    print("\n✅ System initialized successfully!")
    print("\n🌐 Starting web server...")
    print(f"📍 Access the chat interface at: http://localhost:12000")
    print(f"📚 API documentation at: http://localhost:12000/docs")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start the web server
    try:
        import uvicorn
        from ai_agent.web.api import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=12000,
            log_level=settings.log_level.lower(),
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down AI Agent System...")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()