"""
Memory management system for the AI Agent
"""

import sqlite3
import json
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import aiosqlite

from ..core.base import BaseMemory, Message
from ..utils.text_similarity import TextSimilarity


class MemoryManager(BaseMemory):
    """Memory manager with SQLite backend and semantic search"""
    
    def __init__(self, database_url: str, max_memory_size: int = 1000):
        self.database_url = database_url.replace("sqlite:///", "")
        self.max_memory_size = max_memory_size
        self.text_similarity = TextSimilarity()
        self._db_lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the database and create tables"""
        async with aiosqlite.connect(self.database_url) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    metadata TEXT,
                    embedding TEXT
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    metadata TEXT
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages(timestamp DESC)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_role 
                ON messages(role)
            """)
            
            await db.commit()
        
        # Initialize text similarity model
        await self.text_similarity.initialize()
    
    async def store_message(self, message: Message) -> None:
        """Store a message in the database"""
        async with self._db_lock:
            # Generate embedding for semantic search
            embedding = await self.text_similarity.get_embedding(message.content)
            
            async with aiosqlite.connect(self.database_url) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO messages 
                    (id, role, content, timestamp, metadata, embedding)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    message.id,
                    message.role,
                    message.content,
                    message.timestamp.isoformat(),
                    json.dumps(message.metadata) if message.metadata else None,
                    json.dumps(embedding.tolist()) if embedding is not None else None
                ))
                await db.commit()
            
            # Clean up old messages if we exceed max memory size
            await self._cleanup_old_messages()
    
    async def get_conversation_history(self, limit: Optional[int] = None) -> List[Message]:
        """Retrieve conversation history"""
        query = """
            SELECT id, role, content, timestamp, metadata 
            FROM messages 
            ORDER BY timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with aiosqlite.connect(self.database_url) as db:
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
        
        messages = []
        for row in rows:
            metadata = json.loads(row[4]) if row[4] else None
            message = Message(
                id=row[0],
                role=row[1],
                content=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                metadata=metadata
            )
            messages.append(message)
        
        # Return in chronological order
        return list(reversed(messages))
    
    async def clear_memory(self) -> None:
        """Clear all stored memory"""
        async with self._db_lock:
            async with aiosqlite.connect(self.database_url) as db:
                await db.execute("DELETE FROM messages")
                await db.execute("DELETE FROM conversations")
                await db.commit()
    
    async def search_memory(self, query: str, limit: int = 10) -> List[Message]:
        """Search memory for relevant messages using semantic similarity"""
        # Get query embedding
        query_embedding = await self.text_similarity.get_embedding(query)
        if query_embedding is None:
            # Fallback to text search
            return await self._text_search(query, limit)
        
        # Get all messages with embeddings
        async with aiosqlite.connect(self.database_url) as db:
            async with db.execute("""
                SELECT id, role, content, timestamp, metadata, embedding 
                FROM messages 
                WHERE embedding IS NOT NULL
                ORDER BY timestamp DESC
            """) as cursor:
                rows = await cursor.fetchall()
        
        # Calculate similarities
        similarities = []
        for row in rows:
            try:
                embedding = json.loads(row[5])
                similarity = self.text_similarity.cosine_similarity(
                    query_embedding, 
                    embedding
                )
                similarities.append((similarity, row))
            except (json.JSONDecodeError, ValueError):
                continue
        
        # Sort by similarity and get top results
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_results = similarities[:limit]
        
        # Convert to Message objects
        messages = []
        for similarity, row in top_results:
            metadata = json.loads(row[4]) if row[4] else None
            if metadata is None:
                metadata = {}
            metadata['similarity_score'] = similarity
            
            message = Message(
                id=row[0],
                role=row[1],
                content=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                metadata=metadata
            )
            messages.append(message)
        
        return messages
    
    async def _text_search(self, query: str, limit: int = 10) -> List[Message]:
        """Fallback text search using SQL LIKE"""
        async with aiosqlite.connect(self.database_url) as db:
            async with db.execute("""
                SELECT id, role, content, timestamp, metadata 
                FROM messages 
                WHERE content LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"%{query}%", limit)) as cursor:
                rows = await cursor.fetchall()
        
        messages = []
        for row in rows:
            metadata = json.loads(row[4]) if row[4] else None
            message = Message(
                id=row[0],
                role=row[1],
                content=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                metadata=metadata
            )
            messages.append(message)
        
        return messages
    
    async def _cleanup_old_messages(self):
        """Remove old messages if we exceed max memory size"""
        async with aiosqlite.connect(self.database_url) as db:
            # Count current messages
            async with db.execute("SELECT COUNT(*) FROM messages") as cursor:
                count = (await cursor.fetchone())[0]
            
            if count > self.max_memory_size:
                # Delete oldest messages
                messages_to_delete = count - self.max_memory_size
                await db.execute("""
                    DELETE FROM messages 
                    WHERE id IN (
                        SELECT id FROM messages 
                        ORDER BY timestamp ASC 
                        LIMIT ?
                    )
                """, (messages_to_delete,))
                await db.commit()
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        async with aiosqlite.connect(self.database_url) as db:
            # Total messages
            async with db.execute("SELECT COUNT(*) FROM messages") as cursor:
                total_messages = (await cursor.fetchone())[0]
            
            # Messages by role
            async with db.execute("""
                SELECT role, COUNT(*) FROM messages GROUP BY role
            """) as cursor:
                role_counts = dict(await cursor.fetchall())
            
            # Date range
            async with db.execute("""
                SELECT MIN(timestamp), MAX(timestamp) FROM messages
            """) as cursor:
                date_range = await cursor.fetchone()
        
        return {
            "total_messages": total_messages,
            "messages_by_role": role_counts,
            "date_range": {
                "earliest": date_range[0],
                "latest": date_range[1]
            },
            "max_memory_size": self.max_memory_size
        }
    
    async def close(self):
        """Close database connections and cleanup"""
        # SQLite connections are automatically closed
        pass