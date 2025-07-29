import redis
import json
import time
import hashlib
from typing import Dict, Any, Optional, List, Union

class RedisConnector:
    def __init__(self, host='localhost', port=6379, db=0, namespace='echoshell'):
        self.client = redis.StrictRedis(host=host, port=port, db=db)
        self.namespace = namespace
        
    def set_key(self, key, value):
        """Basic key-value storage"""
        try:
            self.client.set(key, value)
            return True
        except Exception as e:
            print(f"Error setting key in Redis: {e}")
            return False

    def get_key(self, key):
        """Basic key retrieval"""
        try:
            value = self.client.get(key)
            return value
        except Exception as e:
            print(f"Error retrieving key from Redis: {e}")
            return None
            
    # --- RedStone Memory Architecture ---
    
    def create_redstone(self, name: str, content: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a RedStone memory crystal with unique hash identifier
        
        RedStones are persistent memory structures that can be referenced across thread boundaries
        and maintain both content and contextual metadata.
        """
        timestamp = time.time()
        metadata = metadata or {}
        
        # Add standard metadata
        metadata.update({
            "created_at": timestamp,
            "last_accessed": timestamp,
            "access_count": 0,
            "namespace": self.namespace
        })
        
        # Create a content hash for cross-reference
        content_str = json.dumps(content) if not isinstance(content, str) else content
        content_hash = hashlib.md5(content_str.encode('utf-8')).hexdigest()[:12]
        
        # Format a unique RedStone key
        redstone_id = f"redstone:{name}.{int(timestamp)}.{content_hash}"
        
        # Prepare the RedStone structure
        redstone = {
            "id": redstone_id,
            "name": name,
            "content": content,
            "metadata": metadata,
            "references": [],
            "resonance": {}  # Emotional/contextual resonance data
        }
        
        # Store in Redis
        self.set_key(redstone_id, json.dumps(redstone))
        
        # Update the RedStone index
        self._update_redstone_index(name, redstone_id)
        
        return redstone_id
    
    def get_redstone(self, redstone_id: str, update_access: bool = True) -> Optional[Dict[str, Any]]:
        """
        Retrieve a RedStone by its ID, optionally updating access metadata
        """
        redstone_data = self.get_key(redstone_id)
        if not redstone_data:
            return None
            
        redstone = json.loads(redstone_data)
        
        if update_access:
            # Update access metadata
            redstone["metadata"]["last_accessed"] = time.time()
            redstone["metadata"]["access_count"] += 1
            self.set_key(redstone_id, json.dumps(redstone))
            
        return redstone
    
    def get_latest_redstone(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent RedStone with the given name
        """
        index_key = f"redstone_index:{name}"
        index_data = self.get_key(index_key)
        
        if not index_data:
            return None
            
        index = json.loads(index_data)
        
        if not index["instances"]:
            return None
            
        # Get the most recent instance (last in the list)
        latest_id = index["instances"][-1]
        return self.get_redstone(latest_id)
    
    def link_redstones(self, source_id: str, target_id: str, link_type: str = "reference") -> bool:
        """
        Create a directional link between two RedStones
        """
        source = self.get_redstone(source_id, update_access=False)
        target = self.get_redstone(target_id, update_access=False)
        
        if not source or not target:
            return False
            
        # Create the reference
        reference = {
            "target_id": target_id,
            "link_type": link_type,
            "created_at": time.time()
        }
        
        # Add to source's references
        source["references"].append(reference)
        self.set_key(source_id, json.dumps(source))
        
        return True
    
    def set_resonance(self, redstone_id: str, resonance_data: Dict[str, float]) -> bool:
        """
        Set emotional/contextual resonance data for a RedStone
        
        Resonance data is typically a mapping of emotional qualities to intensity values
        e.g., {"joy": 0.8, "curiosity": 0.6, "technical": 0.9}
        """
        redstone = self.get_redstone(redstone_id, update_access=False)
        
        if not redstone:
            return False
            
        # Update resonance data
        redstone["resonance"].update(resonance_data)
        self.set_key(redstone_id, json.dumps(redstone))
        
        return True
    
    def _update_redstone_index(self, name: str, redstone_id: str) -> None:
        """
        Update the index of RedStones with a given name
        """
        index_key = f"redstone_index:{name}"
        index_data = self.get_key(index_key)
        
        if index_data:
            index = json.loads(index_data)
            index["instances"].append(redstone_id)
            index["count"] += 1
            index["last_updated"] = time.time()
        else:
            index = {
                "name": name,
                "instances": [redstone_id],
                "count": 1,
                "created_at": time.time(),
                "last_updated": time.time()
            }
            
        self.set_key(index_key, json.dumps(index))
    
    # --- EdgeHub Integration ---
    
    def push_to_edgehub(self, key: str, value: Any, edgehub_client=None) -> bool:
        """
        Push a value to EdgeHub API while maintaining local copy
        
        Requires an initialized EdgeHub client (passed as parameter)
        """
        if edgehub_client is None:
            print("EdgeHub client not provided. Storing locally only.")
            local_key = f"edgehub_pending:{key}"
            self.set_key(local_key, json.dumps({
                "key": key,
                "value": value,
                "timestamp": time.time(),
                "status": "pending"
            }))
            return False
            
        # Store locally first
        local_key = f"edgehub:{key}"
        self.set_key(local_key, json.dumps({
            "key": key,
            "value": value,
            "timestamp": time.time(),
            "status": "synced"
        }))
        
        # Push to EdgeHub
        try:
            edgehub_client.post_memory(key, value)
            return True
        except Exception as e:
            print(f"Error pushing to EdgeHub: {e}")
            # Update status to failed
            local_data = json.loads(self.get_key(local_key))
            local_data["status"] = "failed"
            self.set_key(local_key, json.dumps(local_data))
            return False
    
    def pull_from_edgehub(self, key: str, edgehub_client=None) -> Any:
        """
        Pull a value from EdgeHub API and store locally
        
        Requires an initialized EdgeHub client (passed as parameter)
        """
        if edgehub_client is None:
            print("EdgeHub client not provided. Checking local cache only.")
            local_key = f"edgehub:{key}"
            local_data = self.get_key(local_key)
            return json.loads(local_data)["value"] if local_data else None
            
        # Try to get from EdgeHub
        try:
            result = edgehub_client.get_memory(key)
            
            # Store in local cache
            local_key = f"edgehub:{key}"
            self.set_key(local_key, json.dumps({
                "key": key,
                "value": result,
                "timestamp": time.time(),
                "status": "synced"
            }))
            
            return result
        except Exception as e:
            print(f"Error pulling from EdgeHub: {e}")
            # Try local cache as fallback
            local_key = f"edgehub:{key}"
            local_data = self.get_key(local_key)
            return json.loads(local_data)["value"] if local_data else None

    # --- Langfuse Prompts Integration ---

    def create_langfuse_prompt(self, prompt_name: str, content: Any, metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Create a Langfuse prompt memory entry with enhanced metadata
        
        This is a higher-level function that formats content as a RedStone-compatible
        structure before storing in EdgeHub
        """
        metadata = metadata or {}
        timestamp = time.time()
        
        # Format as RedStone
        redstone_data = {
            "content": content,
            "metadata": {
                **metadata,
                "created_at": timestamp,
                "type": "langfuse_prompt",
                "name": prompt_name
            },
            "references": [],
            "resonance": {}
        }
        
        # Generate a predictable key
        key = f"langfuse_prompt:{prompt_name}.{int(timestamp)}"
        
        # Store in EdgeHub
        success = self.push_to_edgehub(key, redstone_data)
        
        return key if success else None

    def validate_prompt_content(self, content: Any) -> bool:
        """
        Validate the content of a Langfuse prompt
        
        This function checks if the content is accurate and complete before storing it.
        """
        # Implement validation logic here
        if not content:
            return False
        # Add more validation checks as needed
        return True

    def enhance_safeguard_preparation(self) -> None:
        """
        Enhance safeguard preparation by adding new safeguards
        
        This function ensures that reflex safeguards are installed and functioning correctly.
        """
        # Implement safeguard preparation logic here
        pass

    def anchor_real_world_operations(self) -> None:
        """
        Anchor real-world operations before narrations
        
        This function ensures that real-world operations are anchored before any narrations or procedural descriptions.
        """
        # Implement anchoring logic here
        pass

    # --- Narrative Fragments Storage ---

    def store_narrative_fragment(self, fragment_id: str, fragment_data: Dict[str, Any]) -> bool:
        """
        Store a narrative fragment in Redis.
        
        This function stores narrative fragments and their metadata in Redis.
        """
        try:
            self.set_key(f"narrative_fragment:{fragment_id}", json.dumps(fragment_data))
            return True
        except Exception as e:
            print(f"Error storing narrative fragment in Redis: {e}")
            return False

    def get_narrative_fragment(self, fragment_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a narrative fragment from Redis.
        
        This function retrieves narrative fragments and their metadata from Redis.
        """
        try:
            fragment_data = self.get_key(f"narrative_fragment:{fragment_id}")
            return json.loads(fragment_data) if fragment_data else None
        except Exception as e:
            print(f"Error retrieving narrative fragment from Redis: {e}")
            return None
