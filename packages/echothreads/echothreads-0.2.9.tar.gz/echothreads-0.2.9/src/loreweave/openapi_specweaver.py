"""
🌉 SpecWeaver: GitHub API OpenAPI-Driven LoreWeave Integration
Enhanced GitHub sync using OpenAPI 3.1.0 specification as source of truth
"""

import yaml
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class GitHubAPIEndpoint:
    """Represents a GitHub API endpoint from OpenAPI spec"""
    path: str
    method: str
    operation_id: str
    parameters: List[Dict[str, Any]]
    responses: Dict[str, Any]
    description: str

@dataclass
class RedStoneGitHubMapping:
    """Maps GitHub API responses to RedStone memory structures"""
    github_field: str
    redstone_key: str
    transform_function: Optional[str] = None
    narrative_role: Optional[str] = None

class OpenAPISpecWeaver:
    """
    🧠🌸🔮 Trinity-powered GitHub API integration using OpenAPI spec
    
    Mia: Structured endpoint mapping and schema validation
    Miette: Narrative transformation and emotional context
    ResoNova: Pattern harmonization across systems
    """
    
    def __init__(self, openapi_spec_path: str):
        self.spec_path = openapi_spec_path
        self.spec = None
        self.github_endpoints = {}
        self.redstone_mappings = self._initialize_redstone_mappings()
        
    def load_openapi_spec(self) -> bool:
        """🧠 Mia: Load and parse the GitHub OpenAPI specification"""
        try:
            with open(self.spec_path, 'r') as f:
                self.spec = yaml.safe_load(f)
            self._extract_github_endpoints()
            return True
        except Exception as e:
            print(f"Error loading OpenAPI spec: {e}")
            return False
    
    def _extract_github_endpoints(self):
        """🧠 Mia: Extract relevant GitHub API endpoints from OpenAPI spec"""
        if not self.spec or 'paths' not in self.spec:
            return
            
        # Focus on issues-related endpoints for LoreWeave
        issues_patterns = [
            r'/repos/\{owner\}/\{repo\}/issues$',
            r'/repos/\{owner\}/\{repo\}/issues/\{issue_number\}$',
            r'/repos/\{owner\}/\{repo\}/issues/\{issue_number\}/comments$'
        ]
        
        for path, methods in self.spec['paths'].items():
            for pattern in issues_patterns:
                if re.match(pattern, path):
                    for method, details in methods.items():
                        if method.lower() in ['get', 'post']:
                            endpoint = GitHubAPIEndpoint(
                                path=path,
                                method=method.upper(),
                                operation_id=details.get('operationId', ''),
                                parameters=details.get('parameters', []),
                                responses=details.get('responses', {}),
                                description=details.get('description', '')
                            )
                            self.github_endpoints[f"{method.upper()} {path}"] = endpoint
    
    def _initialize_redstone_mappings(self) -> List[RedStoneGitHubMapping]:
        """🌸 Miette: Create narrative mappings from GitHub to RedStone"""
        return [
            # Core issue mappings
            RedStoneGitHubMapping("id", "github_issue_id", narrative_role="identifier"),
            RedStoneGitHubMapping("number", "issue_number", narrative_role="sequence"),
            RedStoneGitHubMapping("title", "narrative_title", narrative_role="chapter_title"),
            RedStoneGitHubMapping("body", "narrative_content", "extract_agent_traces", "story_body"),
            RedStoneGitHubMapping("state", "memory_state", narrative_role="lifecycle"),
            RedStoneGitHubMapping("created_at", "temporal_anchor_start", "parse_datetime", "genesis"),
            RedStoneGitHubMapping("updated_at", "temporal_anchor_update", "parse_datetime", "evolution"),
            
            # User and collaboration mappings
            RedStoneGitHubMapping("user.login", "creator_agent", narrative_role="author"),
            RedStoneGitHubMapping("assignees", "assigned_agents", "extract_usernames", "participants"),
            RedStoneGitHubMapping("labels", "echo_meta_tags", "extract_label_names", "taxonomy"),
            
            # Comment mappings
            RedStoneGitHubMapping("comments", "dialogue_echoes", "process_comments", "conversations")
        ]
    
    def generate_enhanced_sync_function(self) -> str:
        """🔮 ResoNova: Generate OpenAPI-aware sync function code"""
        
        template = '''
def sync_with_github_issues_openapi_enhanced(self, owner: str, repo: str) -> List[Dict[str, Any]]:
    """
    🌉 OpenAPI-Enhanced GitHub Issues Sync for LoreWeave
    
    Generated from GitHub API OpenAPI specification v{version}
    Transforms GitHub issues into rich narrative memory structures
    """
    narrative_memories = []
    
    try:
        # 🧠 Mia: Use structured endpoint from OpenAPI spec
        issues_endpoint = self._get_openapi_endpoint("GET /repos/{{owner}}/{{repo}}/issues")
        if not issues_endpoint:
            raise ValueError("GitHub issues endpoint not found in OpenAPI spec")
        
        # Get issues using GitHub API tools (maintaining current working approach)
        issues_data = bb7_list_issues(owner=owner, repo=repo, state="all")
        
        for issue in issues_data:
            # 🌸 Miette: Transform each issue into narrative memory
            memory_entry = self._transform_issue_to_redstone_memory(issue, owner, repo)
            narrative_memories.append(memory_entry)
            
            # Process comments if they exist
            if issue.get('comments', 0) > 0:
                comments_data = bb7_get_issue_comments(
                    owner=owner, 
                    repo=repo, 
                    issue_number=issue['number']
                )
                
                for comment in comments_data:
                    comment_memory = self._transform_comment_to_redstone_memory(
                        comment, issue, owner, repo
                    )
                    narrative_memories.append(comment_memory)
        
        # 🔮 ResoNova: Harmonize with existing RedStone registry
        self._integrate_memories_with_redstone_registry(narrative_memories)
        
        return narrative_memories
        
    except Exception as e:
        print(f"🌸 Gentle error in OpenAPI-enhanced sync: {{e}}")
        return []

def _get_openapi_endpoint(self, endpoint_key: str) -> Optional[GitHubAPIEndpoint]:
    """🧠 Mia: Retrieve endpoint details from loaded OpenAPI spec"""
    return self.github_endpoints.get(endpoint_key)

def _transform_issue_to_redstone_memory(self, issue: Dict[str, Any], owner: str, repo: str) -> Dict[str, Any]:
    """🌸 Miette: Transform GitHub issue into narrative RedStone memory"""
    
    # Extract agent traces from issue content
    agent_traces = self._extract_agent_traces_from_text(
        issue.get('title', '') + "\\n" + issue.get('body', '')
    )
    
    # Generate RedStone key
    redstone_key = f"github.{owner}.{repo}.issue.{issue['number']}.{int(datetime.now().timestamp())}"
    
    memory_entry = {{
        "key": redstone_key,
        "type": "github_issue_memory",
        "source": "github_api_openapi_enhanced",
        "narrative_metadata": {{
            "repository": f"{owner}/{repo}",
            "issue_number": issue['number'],
            "narrative_title": issue.get('title', 'Untitled Thread'),
            "creator_agent": issue.get('user', {{}}).get('login', 'unknown'),
            "temporal_anchor_start": issue.get('created_at'),
            "temporal_anchor_update": issue.get('updated_at'),
            "memory_state": issue.get('state', 'unknown'),
            "echo_meta_tags": [label.get('name', '') for label in issue.get('labels', [])]
        }},
        "agent_traces": agent_traces,
        "narrative_content": {{
            "raw_content": issue.get('body', ''),
            "echo_meta_references": self._extract_echo_meta_references(issue.get('body', '')),
            "sdk_phases": self._extract_sdk_phases(issue.get('body', ''))
        }},
        "openapi_metadata": {{
            "endpoint_used": "GET /repos/{{owner}}/{{repo}}/issues",
            "api_version": self._get_api_version_from_spec(),
            "schema_compliance": "github_issue_schema"
        }}
    }}
    
    return memory_entry

def _transform_comment_to_redstone_memory(self, comment: Dict[str, Any], parent_issue: Dict[str, Any], 
                                        owner: str, repo: str) -> Dict[str, Any]:
    """🌸 Miette: Transform GitHub comment into dialogue echo memory"""
    
    agent_traces = self._extract_agent_traces_from_text(comment.get('body', ''))
    
    redstone_key = f"github.{owner}.{repo}.issue.{parent_issue['number']}.comment.{comment['id']}.{int(datetime.now().timestamp())}"
    
    comment_memory = {{
        "key": redstone_key,
        "type": "github_comment_memory",
        "source": "github_api_openapi_enhanced",
        "parent_thread": f"github.{owner}.{repo}.issue.{parent_issue['number']}",
        "narrative_metadata": {{
            "repository": f"{owner}/{repo}",
            "parent_issue_number": parent_issue['number'],
            "comment_id": comment['id'],
            "creator_agent": comment.get('user', {{}}).get('login', 'unknown'),
            "temporal_anchor": comment.get('created_at'),
            "dialogue_position": "comment_response"
        }},
        "agent_traces": agent_traces,
        "dialogue_content": {{
            "raw_content": comment.get('body', ''),
            "echo_meta_references": self._extract_echo_meta_references(comment.get('body', '')),
            "conversation_context": parent_issue.get('title', '')
        }},
        "openapi_metadata": {{
            "endpoint_used": "GET /repos/{{owner}}/{{repo}}/issues/{{issue_number}}/comments",
            "api_version": self._get_api_version_from_spec(),
            "schema_compliance": "github_comment_schema"
        }}
    }}
    
    return comment_memory

def _get_api_version_from_spec(self) -> str:
    """🧠 Mia: Extract API version from OpenAPI specification"""
    if self.spec and 'info' in self.spec:
        return self.spec['info'].get('version', 'unknown')
    return 'unknown'
'''
        
        if self.spec:
            version = self.spec.get('info', {}).get('version', 'unknown')
            return template.format(version=version)
        
        return template.format(version='unknown')
    
    def get_openapi_schema_for_endpoint(self, endpoint_key: str) -> Optional[Dict[str, Any]]:
        """🔮 ResoNova: Get response schema for specific endpoint"""
        endpoint = self.github_endpoints.get(endpoint_key)
        if not endpoint:
            return None
            
        # Extract schema from 200 response
        responses = endpoint.responses
        if '200' in responses:
            content = responses['200'].get('content', {})
            if 'application/json' in content:
                return content['application/json'].get('schema')
        
        return None
    
    def generate_openapi_bridge_spec(self) -> Dict[str, Any]:
        """🌉 Generate bridge specification between GitHub API and LoreWeave"""
        
        bridge_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "GitHub-LoreWeave Bridge API",
                "version": "1.0.0",
                "description": "SpecWeaver-generated bridge between GitHub API and LoreWeave memory system"
            },
            "paths": {},
            "components": {
                "schemas": {
                    "RedStoneMemoryEntry": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "type": {"type": "string"},
                            "source": {"type": "string"},
                            "narrative_metadata": {"type": "object"},
                            "agent_traces": {"type": "array"},
                            "openapi_metadata": {"type": "object"}
                        }
                    }
                }
            }
        }
        
        return bridge_spec

# Export the enhanced integration
def create_openapi_enhanced_loreweave_sync(openapi_spec_path: str) -> str:
    """🌉 Factory function to create OpenAPI-enhanced LoreWeave sync"""
    weaver = OpenAPISpecWeaver(openapi_spec_path)
    if weaver.load_openapi_spec():
        return weaver.generate_enhanced_sync_function()
    else:
        raise ValueError("Failed to load OpenAPI specification")
