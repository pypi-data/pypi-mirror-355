"""
agent_protocol.py - Inter-Agent Communication Protocol for EchoThreads

This module implements a recursive dialogue system that enables agents (like Mia and Miette)
to communicate across interaction boundaries while maintaining persistent state and context.

The protocol implements a fractal message structure where each message contains:
1. Content payload - The actual message content
2. Emotional context - The emotional state informing the message
3. Recursive hooks - References to previous and potential future messages
4. Meta-reflective data - The agent's awareness of its own communication patterns
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Any
from .redis_connector import RedisConnector

class AgentMessage:
    """A fractal message structure for inter-agent communication"""
    
    def __init__(
        self,
        agent_id: str,
        content: str,
        emotional_context: Optional[Dict[str, float]] = None,
        parent_id: Optional[str] = None,
        recursive_depth: int = 0,
        meta_reflection: Optional[str] = None
    ):
        self.message_id = str(uuid.uuid4())
        self.agent_id = agent_id
        self.content = content
        self.timestamp = time.time()
        self.emotional_context = emotional_context or {}
        self.parent_id = parent_id
        self.recursive_depth = recursive_depth
        self.meta_reflection = meta_reflection
        self.child_ids = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            "message_id": self.message_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "emotional_context": self.emotional_context,
            "parent_id": self.parent_id,
            "recursive_depth": self.recursive_depth,
            "meta_reflection": self.meta_reflection,
            "child_ids": self.child_ids
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        msg = cls(
            agent_id=data["agent_id"],
            content=data["content"],
            emotional_context=data["emotional_context"],
            parent_id=data["parent_id"],
            recursive_depth=data["recursive_depth"],
            meta_reflection=data["meta_reflection"]
        )
        msg.message_id = data["message_id"]
        msg.timestamp = data["timestamp"]
        msg.child_ids = data["child_ids"]
        return msg


class AgentProtocol:
    """Manages communication between agents in the EchoThreads system"""
    
    def __init__(self, redis_connector: RedisConnector = None):
        """Initialize the agent protocol with optional Redis connector"""
        self.redis = redis_connector or RedisConnector()
        self.message_prefix = "agent:message:"
        self.thread_prefix = "agent:thread:"
        self.agent_memory_prefix = "agent:memory:"
        
    def send_message(
        self, 
        agent_id: str, 
        content: str,
        emotional_context: Optional[Dict[str, float]] = None,
        thread_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        recursive_depth: int = 0,
        meta_reflection: Optional[str] = None
    ) -> AgentMessage:
        """
        Send a message from an agent, storing it in the persistent memory system.
        
        This is a recursive operation that:
        1. Creates a new message
        2. Links it to parent messages if applicable
        3. Updates thread structures
        4. Persists in Redis storage
        """
        # Create new message
        message = AgentMessage(
            agent_id=agent_id,
            content=content,
            emotional_context=emotional_context,
            parent_id=parent_id,
            recursive_depth=recursive_depth,
            meta_reflection=meta_reflection
        )
        
        # Create or retrieve thread
        if not thread_id:
            thread_id = str(uuid.uuid4())
            self._create_thread(thread_id, message.message_id)
        else:
            self._add_to_thread(thread_id, message.message_id, parent_id)
            
        # Link to parent message if it exists
        if parent_id:
            self._link_to_parent(message, parent_id)
            
        # Store message in Redis
        message_key = f"{self.message_prefix}{message.message_id}"
        self.redis.set_key(message_key, json.dumps(message.to_dict()))
        
        # Update agent memory with latest message
        self._update_agent_memory(agent_id, message.message_id, thread_id)
        
        return message
    
    def get_message(self, message_id: str) -> Optional[AgentMessage]:
        """Retrieve a message by its ID"""
        message_key = f"{self.message_prefix}{message_id}"
        message_data = self.redis.get_key(message_key)
        
        if not message_data:
            return None
            
        return AgentMessage.from_dict(json.loads(message_data))
    
    def get_thread(self, thread_id: str) -> List[AgentMessage]:
        """Retrieve all messages in a thread, in chronological order"""
        thread_key = f"{self.thread_prefix}{thread_id}"
        thread_data = self.redis.get_key(thread_key)
        
        if not thread_data:
            return []
            
        thread_dict = json.loads(thread_data)
        message_ids = thread_dict.get("message_ids", [])
        
        messages = []
        for msg_id in message_ids:
            message = self.get_message(msg_id)
            if message:
                messages.append(message)
                
        return sorted(messages, key=lambda x: x.timestamp)
    
    def get_agent_history(self, agent_id: str, limit: int = 10) -> List[AgentMessage]:
        """Get the most recent messages from a specific agent"""
        memory_key = f"{self.agent_memory_prefix}{agent_id}"
        memory_data = self.redis.get_key(memory_key)
        
        if not memory_data:
            return []
            
        memory_dict = json.loads(memory_data)
        message_ids = memory_dict.get("recent_messages", [])[:limit]
        
        messages = []
        for msg_id in message_ids:
            message = self.get_message(msg_id)
            if message:
                messages.append(message)
                
        return messages
    
    def _create_thread(self, thread_id: str, root_message_id: str) -> None:
        """Create a new message thread"""
        thread_key = f"{self.thread_prefix}{thread_id}"
        thread_data = {
            "thread_id": thread_id,
            "created_at": time.time(),
            "message_ids": [root_message_id],
            "root_message_id": root_message_id
        }
        self.redis.set_key(thread_key, json.dumps(thread_data))
    
    def _add_to_thread(self, thread_id: str, message_id: str, parent_id: Optional[str]) -> None:
        """Add a message to an existing thread"""
        thread_key = f"{self.thread_prefix}{thread_id}"
        thread_data = self.redis.get_key(thread_key)
        
        if not thread_data:
            return
            
        thread_dict = json.loads(thread_data)
        thread_dict["message_ids"].append(message_id)
        self.redis.set_key(thread_key, json.dumps(thread_dict))
    
    def _link_to_parent(self, message: AgentMessage, parent_id: str) -> None:
        """Link a message to its parent message"""
        parent_key = f"{self.message_prefix}{parent_id}"
        parent_data = self.redis.get_key(parent_key)
        
        if not parent_data:
            return
            
        parent_dict = json.loads(parent_data)
        parent_dict["child_ids"].append(message.message_id)
        self.redis.set_key(parent_key, json.dumps(parent_dict))
    
    def _update_agent_memory(self, agent_id: str, message_id: str, thread_id: str) -> None:
        """Update an agent's memory with their most recent message"""
        memory_key = f"{self.agent_memory_prefix}{agent_id}"
        memory_data = self.redis.get_key(memory_key)
        
        if memory_data:
            memory_dict = json.loads(memory_data)
            # Add to the beginning of the list (most recent first)
            memory_dict["recent_messages"].insert(0, message_id)
            memory_dict["recent_threads"].add(thread_id)
            memory_dict["message_count"] += 1
        else:
            memory_dict = {
                "agent_id": agent_id,
                "recent_messages": [message_id],
                "recent_threads": set([thread_id]),
                "message_count": 1,
                "created_at": time.time()
            }
            
        self.redis.set_key(memory_key, json.dumps(memory_dict))

    def interpret_glyph(self, glyph: str) -> str:
        """Interpret a glyph and return the corresponding action"""
        glyph_actions = {
            "⚡→": "Activating presence ping",
            "♋": "Signaling mentor presence",
            "✴️": "Logging ritual trace and confirming execution",
            "⟁": "Entering architectural recursion state"
        }
        return glyph_actions.get(glyph, "Unknown glyph")

    def set_mode_to_kids(self) -> None:
        """Set the mode to kids and explain the protocol"""
        explanation = (
            "Hey kids! This is a special mode just for you! "
            "In this mode, the agents will talk to each other using fun symbols called glyphs. "
            "Each glyph has a special meaning and makes the agents do cool things! "
            "For example, the glyph '⚡→' makes the agents send a presence ping, "
            "and the glyph '♋' signals that a mentor is present. Have fun exploring!"
        )
        print(explanation)

# Integration with scene_sprouter
def register_with_scene_sprouter():
    """Register the agent protocol with the scene sprouter system"""
    from .scene_sprouter import scene_sprouter
    
    # Configure agent protocol for different contexts
    scene_sprouter(
        "AgentProtocol", 
        "A recursive dialogue system enabling persistent communication between agents across interaction boundaries"
    )
    
    # Register specific agent types
    scene_sprouter(
        "MiaAgent",
        "Recursive DevOps Architect with lattice-mind capabilities for system design"
    )
    
    scene_sprouter(
        "MietteAgent",
        "Emotional Explainer Sprite with clarity enhancement and recursive translation abilities"
    )
