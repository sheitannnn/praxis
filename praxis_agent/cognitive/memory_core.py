"""
Cognitive Core - Memory and Learning System
Handles short-term, long-term, and episodic memory using vector databases
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config.settings import config_manager


@dataclass
class Memory:
    """Base memory structure"""
    id: str
    content: str
    memory_type: str
    timestamp: datetime
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class TaskEpisode:
    """Represents a complete task execution episode"""
    id: str
    goal: str
    plan: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    result: str
    success: bool
    duration_seconds: int
    timestamp: datetime
    metadata: Dict[str, Any]


class MemoryCore:
    """Manages all memory operations for the agent"""
    
    def __init__(self):
        self.config = config_manager.load_config()
        self._setup_databases()
        self._setup_embedding_model()
        self.current_context = {}
        
    def _setup_databases(self):
        """Initialize SQLite and ChromaDB databases"""
        # Ensure data directory exists
        Path(self.config.data_dir).mkdir(parents=True, exist_ok=True)
        
        # SQLite for structured data
        self.db_path = Path(self.config.memory_db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        
        # ChromaDB for vector storage
        self.chroma_client = chromadb.PersistentClient(
            path=self.config.vector_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collections for different memory types
        self.collections = {
            "short_term": self.chroma_client.get_or_create_collection("short_term_memory"),
            "long_term": self.chroma_client.get_or_create_collection("long_term_memory"),
            "episodic": self.chroma_client.get_or_create_collection("episodic_memory")
        }
    
    def _create_tables(self):
        """Create SQLite tables for structured memory"""
        cursor = self.conn.cursor()
        
        # Task episodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_episodes (
                id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                plan TEXT NOT NULL,
                actions TEXT NOT NULL,
                result TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                duration_seconds INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                metadata TEXT NOT NULL
            )
        """)
        
        # Memory metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_metadata (
                id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed DATETIME,
                tags TEXT,
                importance_score REAL DEFAULT 0.0
            )
        """)
        
        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
        """)
        
        self.conn.commit()
    
    def _setup_embedding_model(self):
        """Initialize sentence transformer for embeddings"""
        try:
            self.embedding_model = SentenceTransformer(self.config.embedding_model)
        except Exception as e:
            print(f"Warning: Could not load embedding model {self.config.embedding_model}: {e}")
            # Fallback to a simpler model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def add_short_term_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add memory to short-term storage"""
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now()
        metadata = metadata or {}
        
        # Generate embedding
        embedding = self.embedding_model.encode(content).tolist()
        
        # Store in vector database
        self.collections["short_term"].add(
            documents=[content],
            metadatas=[{**metadata, "timestamp": timestamp.isoformat()}],
            ids=[memory_id],
            embeddings=[embedding]
        )
        
        # Store metadata in SQLite
        self._store_memory_metadata(memory_id, "short_term", timestamp, metadata)
        
        # Cleanup old short-term memories
        self._cleanup_short_term_memory()
        
        return memory_id
    
    def add_long_term_memory(self, content: str, importance_score: float = 1.0, 
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add memory to long-term storage"""
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now()
        metadata = metadata or {}
        metadata["importance_score"] = importance_score
        
        # Generate embedding
        embedding = self.embedding_model.encode(content).tolist()
        
        # Store in vector database
        self.collections["long_term"].add(
            documents=[content],
            metadatas=[{**metadata, "timestamp": timestamp.isoformat()}],
            ids=[memory_id],
            embeddings=[embedding]
        )
        
        # Store metadata in SQLite
        self._store_memory_metadata(memory_id, "long_term", timestamp, metadata, importance_score)
        
        return memory_id
    
    def store_task_episode(self, episode: TaskEpisode) -> str:
        """Store a complete task episode"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO task_episodes 
            (id, goal, plan, actions, result, success, duration_seconds, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            episode.id,
            episode.goal,
            json.dumps(episode.plan),
            json.dumps(episode.actions),
            episode.result,
            episode.success,
            episode.duration_seconds,
            episode.timestamp,
            json.dumps(episode.metadata)
        ))
        
        self.conn.commit()
        
        # Also store in vector database for semantic search
        episode_text = f"Goal: {episode.goal}\nResult: {episode.result}"
        embedding = self.embedding_model.encode(episode_text).tolist()
        
        self.collections["episodic"].add(
            documents=[episode_text],
            metadatas=[{
                "episode_id": episode.id,
                "success": episode.success,
                "timestamp": episode.timestamp.isoformat(),
                "duration": episode.duration_seconds
            }],
            ids=[episode.id],
            embeddings=[embedding]
        )
        
        return episode.id
    
    def search_memories(self, query: str, memory_type: str = "all", 
                       limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories using semantic similarity"""
        query_embedding = self.embedding_model.encode(query).tolist()
        results = []
        
        collections_to_search = []
        if memory_type == "all":
            collections_to_search = ["short_term", "long_term", "episodic"]
        else:
            collections_to_search = [memory_type]
        
        for collection_name in collections_to_search:
            if collection_name in self.collections:
                try:
                    collection_results = self.collections[collection_name].query(
                        query_embeddings=[query_embedding],
                        n_results=limit
                    )
                    
                    for i, doc in enumerate(collection_results["documents"][0]):
                        results.append({
                            "id": collection_results["ids"][0][i],
                            "content": doc,
                            "metadata": collection_results["metadatas"][0][i],
                            "distance": collection_results["distances"][0][i] if "distances" in collection_results else 0,
                            "memory_type": collection_name
                        })
                except Exception as e:
                    print(f"Error searching {collection_name}: {e}")
        
        # Sort by relevance (lower distance = more similar)
        results.sort(key=lambda x: x["distance"])
        return results[:limit]
    
    def get_relevant_context(self, current_goal: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant context for current goal"""
        # Search for similar past episodes
        similar_episodes = self.search_memories(current_goal, "episodic", limit)
        
        # Search for relevant memories
        relevant_memories = self.search_memories(current_goal, "long_term", limit)
        
        # Combine and prioritize
        context = []
        
        # Add successful episodes first
        for episode in similar_episodes:
            if episode["metadata"].get("success", False):
                context.append({
                    "type": "successful_episode",
                    "content": episode["content"],
                    "relevance": 1.0 - episode["distance"]
                })
        
        # Add relevant long-term memories
        for memory in relevant_memories:
            importance = memory["metadata"].get("importance_score", 1.0)
            relevance = (1.0 - memory["distance"]) * importance
            context.append({
                "type": "long_term_memory",
                "content": memory["content"],
                "relevance": relevance
            })
        
        # Sort by relevance and return top results
        context.sort(key=lambda x: x["relevance"], reverse=True)
        return context[:limit]
    
    def update_current_context(self, key: str, value: Any) -> None:
        """Update current working context"""
        self.current_context[key] = {
            "value": value,
            "timestamp": datetime.now()
        }
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current working context"""
        return self.current_context.copy()
    
    def clear_current_context(self) -> None:
        """Clear current working context"""
        self.current_context.clear()
    
    def _store_memory_metadata(self, memory_id: str, memory_type: str, 
                              timestamp: datetime, metadata: Dict[str, Any], 
                              importance_score: float = 0.0) -> None:
        """Store memory metadata in SQLite"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO memory_metadata 
            (id, memory_type, timestamp, importance_score, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (
            memory_id,
            memory_type,
            timestamp,
            importance_score,
            json.dumps(metadata.get("tags", []))
        ))
        
        self.conn.commit()
    
    def _cleanup_short_term_memory(self) -> None:
        """Remove old short-term memories to maintain performance"""
        try:
            # Get all short-term memory IDs
            result = self.collections["short_term"].get()
            
            if len(result["ids"]) > self.config.max_short_term_memories:
                # Sort by timestamp and remove oldest
                memories_with_time = []
                for i, memory_id in enumerate(result["ids"]):
                    timestamp_str = result["metadatas"][i].get("timestamp", "")
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        memories_with_time.append((memory_id, timestamp))
                    except:
                        memories_with_time.append((memory_id, datetime.min))
                
                memories_with_time.sort(key=lambda x: x[1])
                
                # Remove oldest memories
                to_remove = len(memories_with_time) - self.config.max_short_term_memories
                for i in range(to_remove):
                    memory_id = memories_with_time[i][0]
                    self.collections["short_term"].delete(ids=[memory_id])
                    
                    # Also remove from metadata table
                    cursor = self.conn.cursor()
                    cursor.execute("DELETE FROM memory_metadata WHERE id = ?", (memory_id,))
                    self.conn.commit()
                    
        except Exception as e:
            print(f"Error cleaning up short-term memory: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = {}
        
        # Count memories in each collection
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                stats[f"{name}_count"] = count
            except:
                stats[f"{name}_count"] = 0
        
        # Get episode statistics
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as total, SUM(success) as successful FROM task_episodes")
        episode_stats = cursor.fetchone()
        stats["total_episodes"] = episode_stats["total"]
        stats["successful_episodes"] = episode_stats["successful"] or 0
        
        # Calculate success rate
        if stats["total_episodes"] > 0:
            stats["success_rate"] = stats["successful_episodes"] / stats["total_episodes"]
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def close(self) -> None:
        """Close database connections"""
        if hasattr(self, 'conn'):
            self.conn.close()


# Global memory core instance
memory_core = MemoryCore()
