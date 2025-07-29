#!/usr/bin/env python3
"""
🧩 git_pr_binder.py — CLI extension for EchoShell

This tool creates dynamic bindings between Git branch contexts, GitHub Pull Requests,
and Mia's Recursive Arcs. It enables seamless integration of development workflows 
with the narrative lattice of the EchoShell framework.

Usage:
    activate binder [--branch=<name>] [--pr=<number>] [--owner=<name>]
    status          - Show current bindings
    help            - Show this help message
"""

import os
import sys
import json
import time
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union

# Constants
DEFAULT_PR_PATTERN = r"jgwill#EchoThreads#(\d+)"
DEFAULT_REDSTONE_PREFIX = "redstones:M"
DEFAULT_CONTEXT_PREFIX = "Mia::Context:EchoThreads.PR"
DEFAULT_SNAPSHOT_PREFIX = "Mia::Snapshots:EchoThreads.PR"

class GitPRBinder:
    """Core implementation of Git PR binding functionality"""
    
    def __init__(self, git_dir: Optional[str] = None):
        """Initialize the GitPRBinder with optional git directory"""
        self.git_dir = git_dir or self._find_git_dir()
        self.timestamp = int(time.time())
        self.date_str = datetime.now().strftime("%Y%m%d")
        
    def _find_git_dir(self) -> Optional[str]:
        """Find the .git directory by walking up from current directory"""
        current_dir = os.getcwd()
        while current_dir != '/':
            git_dir = os.path.join(current_dir, ".git")
            if os.path.isdir(git_dir):
                return git_dir
            current_dir = os.path.dirname(current_dir)
        return None
        
    def get_current_branch(self) -> Optional[str]:
        """Get the name of the current git branch"""
        if not self.git_dir:
            return None
            
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.SubprocessError:
            return None
            
    def get_config_value(self, key: str) -> Optional[str]:
        """Get a specific git config value"""
        if not self.git_dir:
            return None
            
        try:
            result = subprocess.run(
                ["git", "config", "--get", key],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except subprocess.SubprocessError:
            return None
            
    def set_config_value(self, key: str, value: str) -> bool:
        """Set a specific git config value"""
        if not self.git_dir:
            return False
            
        try:
            subprocess.run(
                ["git", "config", key, value],
                check=True
            )
            return True
        except subprocess.SubprocessError:
            return False
            
    def get_branch_pr_metadata(self, branch: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Extract PR metadata from branch configuration"""
        if not self.git_dir:
            return None
            
        branch = branch or self.get_current_branch()
        if not branch:
            return None
            
        # Get the github-pr-owner-number value from branch config
        pr_value = self.get_config_value(f"branch.{branch}.github-pr-owner-number")
        if not pr_value:
            return None
            
        # Parse the value using the default pattern
        match = re.match(DEFAULT_PR_PATTERN, pr_value)
        if not match:
            # Try to extract any numbers as PR number
            nums = re.findall(r'\d+', pr_value)
            if nums:
                pr_number = nums[0]
                owner = pr_value.split('#')[0] if '#' in pr_value else "unknown"
                return {
                    "owner": owner,
                    "pr_number": pr_number,
                    "value": pr_value
                }
            return None
            
        # Extract PR number from the pattern
        pr_number = match.group(1)
        owner = "jgwill"  # Default owner from the pattern
        
        return {
            "owner": owner,
            "pr_number": pr_number,
            "value": pr_value
        }
        
    def set_branch_pr_metadata(self, branch: str, owner: str, pr_number: str) -> bool:
        """Set PR metadata for a branch"""
        if not self.git_dir:
            return False
            
        # Format the metadata value
        value = f"{owner}#EchoThreads#{pr_number}"
        
        # Set the config value
        return self.set_config_value(f"branch.{branch}.github-pr-owner-number", value)
        
    def create_redstone(self, name: str, content: Any) -> str:
        """Create a simple RedStone memory record in local file"""
        timestamp = int(time.time())
        redstone_id = f"{DEFAULT_REDSTONE_PREFIX}.{self.date_str}.{timestamp}.Guillaume.Mia.Arc.CodingRecursiveDevOpsV6.Tool.GitPRBinder"
        
        redstone = {
            "id": redstone_id,
            "name": name,
            "content": content,
            "timestamp": timestamp,
            "metadata": {
                "tool": "GitPRBinder",
                "creator": "Guillaume",
                "arc": "Mia.Arc.CodingRecursiveDevOpsV6"
            }
        }
        
        # Create aureon cache directory if it doesn't exist
        cache_dir = os.path.expanduser("~/.aureon/cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Write the redstone to a JSON file
        cache_file = os.path.join(cache_dir, f"{name}.{timestamp}.json")
        with open(cache_file, "w") as f:
            json.dump(redstone, f, indent=2)
        
        print(f"🧠 Created RedStone: {redstone_id}")
        print(f"📝 Cache file: {cache_file}")
        
        return redstone_id
        
    def activate_binding(self, branch: Optional[str] = None, owner: Optional[str] = None, pr_number: Optional[str] = None) -> bool:
        """Activate the binding between Git branch, PR, and Mia Arc"""
        if not self.git_dir:
            print("❌ No Git repository found. Please run from a Git repository.")
            return False
            
        # Get current branch if not specified
        branch = branch or self.get_current_branch()
        if not branch:
            print("❌ Could not determine current branch.")
            return False
            
        # Get PR metadata from branch config if not provided
        pr_metadata = None
        if not (owner and pr_number):
            pr_metadata = self.get_branch_pr_metadata(branch)
            
        # Use provided values or metadata
        if pr_metadata:
            owner = owner or pr_metadata["owner"]
            pr_number = pr_number or pr_metadata["pr_number"]
        elif not (owner and pr_number):
            print("❌ PR metadata not found in branch config and not provided.")
            return False
            
        # Ensure branch has PR metadata
        if not pr_metadata:
            self.set_branch_pr_metadata(branch, owner, pr_number)
            
        # Create context and snapshot identifiers
        context_id = f"{DEFAULT_CONTEXT_PREFIX}{pr_number}"
        snapshot_id = f"{DEFAULT_SNAPSHOT_PREFIX}{pr_number}.GoalContext.{self.timestamp}"
        
        # Create binding content
        binding_content = {
            "branch": branch,
            "owner": owner,
            "pr_number": pr_number,
            "git_dir": self.git_dir,
            "timestamp": self.timestamp,
            "context_id": context_id,
            "snapshot_id": snapshot_id
        }
        
        # Create the RedStone
        redstone_id = self.create_redstone(
            f"git_pr_binding.{branch}.{pr_number}",
            binding_content
        )
        
        print(f"""
🧩 GitPRBinder activated successfully!
✅ Branch: {branch}
✅ PR: {owner}#EchoThreads#{pr_number}
✅ Context ID: {context_id}
✅ Snapshot ID: {snapshot_id}
✅ RedStone: {redstone_id}
""")
        
        return True
    
    def show_status(self) -> None:
        """Show current binding status"""
        if not self.git_dir:
            print("❌ No Git repository found. Please run from a Git repository.")
            return
            
        branch = self.get_current_branch()
        if not branch:
            print("❌ Could not determine current branch.")
            return
            
        print(f"\n🧩 GitPRBinder Status for branch: {branch}")
        
        pr_metadata = self.get_branch_pr_metadata(branch)
        if pr_metadata:
            print(f"""
✅ PR Metadata found:
   Owner: {pr_metadata["owner"]}
   PR Number: {pr_metadata["pr_number"]}
   Raw Value: {pr_metadata["value"]}
   
🔗 Context ID: {DEFAULT_CONTEXT_PREFIX}{pr_metadata["pr_number"]}
🔗 Latest Snapshot ID: {DEFAULT_SNAPSHOT_PREFIX}{pr_metadata["pr_number"]}.GoalContext.*
""")
        else:
            print("""
❌ No PR metadata found for this branch.
   To add metadata, use: activate binder --owner=<name> --pr=<number>
""")


def handle_command(args: list) -> int:
    """Process command line arguments"""
    if not args or args[0] == "help":
        print(__doc__)
        return 0
        
    binder = GitPRBinder()
    
    if args[0] == "activate" and args[1] == "binder":
        # Parse optional arguments
        branch = None
        owner = None
        pr_number = None
        
        for arg in args[2:]:
            if arg.startswith("--branch="):
                branch = arg.split("=", 1)[1]
            elif arg.startswith("--owner="):
                owner = arg.split("=", 1)[1]
            elif arg.startswith("--pr="):
                pr_number = arg.split("=", 1)[1]
                
        return 0 if binder.activate_binding(branch, owner, pr_number) else 1
        
    elif args[0] == "status":
        binder.show_status()
        return 0
        
    else:
        print(f"❌ Unknown command: {args[0]}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    # Remove script name from arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Process command
    if args and args[0] == "now":
        # Special case for "activate binder now"
        if len(args) >= 3 and args[0] == "activate" and args[1] == "binder" and args[2] == "now":
            # Convert to standard form without "now"
            args = args[:2] + args[3:]
            
    # Handle the command
    sys.exit(handle_command(args))