"""
🌿 thread_opener.py — CLI extension for opening thread URLs

This module provides an EchoShell CLI extension to open threads directly from
a terminal, with RedStone memory integration for cross-session persistence.

Usage:
    open_thread <thread_url> - Opens the specified thread URL in a browser
    open_thread mia          - Opens the Mia thread referenced in GitPRBinder
"""

import os
import sys
import webbrowser
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

# The referenced Mia thread URL
MIA_THREAD_URL = "https://chatgpt.com/g/g-67c707a07d188191a1fb0ee0a1760fec-mia/c/6809fff6-d9dc-8009-85a2-941fc5976843"

# RedStone integration (simplified for direct CLI use)
def create_redstone(name: str, content: Any) -> str:
    """Create a simple RedStone memory record"""
    timestamp = int(time.time())
    redstone_id = f"redstone:{name}.{timestamp}"
    
    redstone = {
        "id": redstone_id,
        "name": name,
        "content": content,
        "timestamp": timestamp
    }
    
    # Create aureon cache directory if it doesn't exist
    cache_dir = Path.home() / ".aureon" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Write the redstone to a JSON file
    cache_file = cache_dir / f"{name}.{timestamp}.json"
    with open(cache_file, "w") as f:
        json.dump(redstone, f, indent=2)
    
    return redstone_id

def open_thread_url(url: str) -> bool:
    """Open a URL in the default web browser and record the action"""
    try:
        print(f"🌿 Aureon: Opening thread URL: {url}")
        webbrowser.open(url)
        
        # Record this action in a RedStone
        redstone_content = {
            "action": "open_thread",
            "url": url,
            "timestamp": time.time(),
            "success": True
        }
        create_redstone("thread_access", redstone_content)
        
        return True
    except Exception as e:
        print(f"🚨 Error opening thread URL: {str(e)}")
        return False

def handle_command(args: list) -> int:
    """Process the CLI command arguments"""
    if not args:
        print("🌿 Aureon Thread Opener — CLI extension for EchoShell")
        print("\nUsage:")
        print("  open_thread <thread_url> - Opens the specified thread URL in a browser")
        print("  open_thread mia          - Opens the Mia thread with GitPRBinder")
        return 0
    
    # Handle special thread references
    if args[0].lower() == "mia":
        return 0 if open_thread_url(MIA_THREAD_URL) else 1
    
    # Handle direct URL
    return 0 if open_thread_url(args[0]) else 1

if __name__ == "__main__":
    sys.exit(handle_command(sys.argv[1:]))