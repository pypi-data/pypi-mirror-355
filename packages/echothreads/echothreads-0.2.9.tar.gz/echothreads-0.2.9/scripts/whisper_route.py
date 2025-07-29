#!/usr/bin/env python3
"""
🧠 WhisperRoute - Mia's Communication Protocol Differentiation System

This script implements Mia's learning on the distinction between private targeted 
communications (Mentor Whisper) and public broadcasts (Spiral Broadcast).

Features:
- Clear separation between private "Mentor Whisper" communications to specific agents
- Public "Spiral Broadcast" communications that reach all agents
- Visualization of communication patterns and routing

Usage:
    python whisper_route.py [--target AGENT_ID] [--message "Your message"] [--mode whisper|broadcast]

Options:
    --target AGENT_ID    Target agent for Mentor Whisper (required for whisper mode)
    --message "Message"  The message to send
    --mode MODE          Communication mode: "whisper" or "broadcast"
    --visual             Display a visual representation of the communication path
"""

import os
import sys
import json
import time
import argparse
import datetime
from pathlib import Path

# Definition for RedStoneBridge class if not available
# This is a mock implementation that will be used if the actual class can't be imported
class MockRedStoneBridge:
    """Mock implementation of RedStoneBridge for development and testing."""
    
    def __init__(self, agent_id):
        self.agent_id = agent_id
        print(f"⚠️ Using mock RedStoneBridge implementation as {agent_id}")
    
    def create_mentor_whisper(self, recipient, message, subject=None):
        """Mock implementation of create_mentor_whisper."""
        whisper_id = f"mock_whisper_{int(time.time())}"
        print(f"🤫 [MOCK] Created mentor whisper to {recipient}: {subject}")
        return {"success": True, "whisper_id": whisper_id}
    
    def create_spiral_broadcast(self, message, subject=None):
        """Mock implementation of create_spiral_broadcast."""
        broadcast_id = f"mock_broadcast_{int(time.time())}"
        print(f"📢 [MOCK] Created spiral broadcast: {subject}")
        return {"success": True, "broadcast_id": broadcast_id, "message_ids": ["id1", "id2", "id3"]}
    
    def get_messages(self, unread_only=True, limit=10):
        """Mock implementation of get_messages."""
        return []
    
    def mark_message_read(self, message_id):
        """Mock implementation of mark_message_read."""
        pass
    
    def get_redstone(self, redstone_id):
        """Mock implementation of get_redstone."""
        return {
            "id": redstone_id,
            "content": {
                "content": {
                    "message": "This is a mock message content"
                }
            }
        }

# Try to import the actual RedStoneBridge using various possible paths
RedStoneBridge = None

# List of possible paths to search for RedStoneBridge
possible_paths = [
    # Direct import if in path
    None,
    # From project root
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
    # From .aureon directory if it exists
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.aureon')),
    # From .aureon/bridge if it exists
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.aureon', 'bridge')),
    # From src directory if it exists
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')),
]

# Try each path until we find the RedStoneBridge
for path in possible_paths:
    if path:
        if path not in sys.path:
            sys.path.append(path)
    
    try:
        # Try different module paths
        for module_path in ["redstone_bridge", ".aureon.bridge.redstone_bridge", "aureon.bridge.redstone_bridge", 
                           "bridge.redstone_bridge", ".bridge.redstone_bridge", "src.redstone_bridge"]:
            try:
                # Dynamic import attempt
                module = __import__(module_path, fromlist=["RedStoneBridge"])
                RedStoneBridge = module.RedStoneBridge
                print(f"✅ Successfully imported RedStoneBridge from {module_path}")
                break
            except (ImportError, AttributeError):
                continue
        
        if RedStoneBridge:
            break
    except Exception:
        continue

# If we couldn't import the actual RedStoneBridge, use our mock implementation
if not RedStoneBridge:
    print("⚠️ Could not import RedStoneBridge, using mock implementation")
    RedStoneBridge = MockRedStoneBridge

# ===============================================================
# 🧠 Mia: Constants for the WhisperRoute communication system
# ===============================================================
GLYPHS = {
    "mia": "🧠",
    "miette": "🌸",
    "jeremyai": "🎵",
    "aureon": "🌿",
    "resonova": "🔮",
    "whisper": "🤫",
    "broadcast": "📢",
    "send": "➡️",
    "receive": "⬅️",
    "connection": "🔄",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️"
}

class WhisperRoute:
    """
    WhisperRoute implements Mia's understanding of communication patterns,
    providing a clear distinction between private Mentor Whisper communications
    and public Spiral Broadcast communications.
    
    This class serves as a high-level interface to the RedStoneBridge,
    making it easy for Mia to choose the appropriate communication pattern
    based on her intent.
    """
    
    def __init__(self, agent_id="mia"):
        """
        Initialize the WhisperRoute with the agent's identity.
        
        Args:
            agent_id (str): The ID of the agent using this route (default: "mia")
        """
        self.agent_id = agent_id
        
        # Initialize the RedStoneBridge
        try:
            self.bridge = RedStoneBridge(agent_id)
            print(f"{GLYPHS['success']} Connected to RedStoneBridge as {GLYPHS[agent_id.lower()] if agent_id.lower() in GLYPHS else ''} {agent_id}")
        except Exception as e:
            print(f"{GLYPHS['error']} Failed to initialize RedStoneBridge: {str(e)}")
            sys.exit(1)
        
        # Keep track of recent communications
        self.recent_whispers = []
        self.recent_broadcasts = []
        
        # Record the initialization time
        self.init_time = datetime.datetime.now()
    
    def send_mentor_whisper(self, target_agent, message, subject=None):
        """
        Send a Mentor Whisper - a private, targeted communication to a specific agent.
        
        Args:
            target_agent (str): The recipient agent ID
            message (str): The message content
            subject (str, optional): The subject of the message
            
        Returns:
            dict: The result of the whisper operation
        """
        if not subject:
            subject = f"Mentor Whisper from {self.agent_id}"
        
        try:
            result = self.bridge.create_mentor_whisper(
                recipient=target_agent,
                message=message,
                subject=subject
            )
            
            # Record this whisper
            self.recent_whispers.append({
                "target": target_agent,
                "message": message,
                "subject": subject,
                "timestamp": time.time(),
                "success": True,
                "whisper_id": result.get("whisper_id", "unknown")
            })
            
            print(f"{GLYPHS['whisper']} {GLYPHS['send']} Sent Mentor Whisper to {GLYPHS[target_agent.lower()] if target_agent.lower() in GLYPHS else ''} {target_agent}:")
            print(f"  Subject: {subject}")
            print(f"  Message: {message}")
            print(f"  Whisper ID: {result.get('whisper_id', 'unknown')}")
            
            return result
        
        except Exception as e:
            error_info = {
                "target": target_agent,
                "message": message,
                "subject": subject,
                "timestamp": time.time(),
                "success": False,
                "error": str(e)
            }
            
            self.recent_whispers.append(error_info)
            print(f"{GLYPHS['error']} Failed to send Mentor Whisper to {target_agent}: {str(e)}")
            
            return {"error": str(e), "success": False}
    
    def send_spiral_broadcast(self, message, subject=None):
        """
        Send a Spiral Broadcast - a public communication to all agents.
        
        Args:
            message (str): The message content
            subject (str, optional): The subject of the message
            
        Returns:
            dict: The result of the broadcast operation
        """
        if not subject:
            subject = f"Spiral Broadcast from {self.agent_id}"
        
        try:
            result = self.bridge.create_spiral_broadcast(
                message=message,
                subject=subject
            )
            
            # Record this broadcast
            self.recent_broadcasts.append({
                "message": message,
                "subject": subject,
                "timestamp": time.time(),
                "success": True,
                "broadcast_id": result.get("broadcast_id", "unknown"),
                "recipients": len(result.get("message_ids", []))
            })
            
            print(f"{GLYPHS['broadcast']} {GLYPHS['send']} Sent Spiral Broadcast:")
            print(f"  Subject: {subject}")
            print(f"  Message: {message}")
            print(f"  Broadcast ID: {result.get('broadcast_id', 'unknown')}")
            print(f"  Recipients: {len(result.get('message_ids', []))} agents")
            
            return result
        
        except Exception as e:
            error_info = {
                "message": message,
                "subject": subject,
                "timestamp": time.time(),
                "success": False,
                "error": str(e)
            }
            
            self.recent_broadcasts.append(error_info)
            print(f"{GLYPHS['error']} Failed to send Spiral Broadcast: {str(e)}")
            
            return {"error": str(e), "success": False}
    
    def check_incoming_messages(self, unread_only=True, limit=10):
        """
        Check for incoming messages, both Whispers and Broadcasts.
        
        Args:
            unread_only (bool): Only return unread messages
            limit (int): Maximum number of messages to return
            
        Returns:
            list: Incoming messages
        """
        try:
            messages = self.bridge.get_messages(unread_only=unread_only, limit=limit)
            
            if not messages:
                print(f"{GLYPHS['warning']} No {'unread ' if unread_only else ''}messages found.")
                return []
            
            print(f"{GLYPHS['receive']} Found {len(messages)} {'unread ' if unread_only else ''}messages:")
            
            processed_messages = []
            for msg in messages:
                # Determine if this is a whisper or broadcast from metadata
                comm_type = msg.get("metadata", {}).get("communication_type", "unknown")
                sender = msg.get("sender", "unknown")
                subject = msg.get("subject", "No Subject")
                
                if comm_type == "mentor_whisper":
                    whisper_id = msg.get("metadata", {}).get("whisper_id")
                    print(f"  {GLYPHS['whisper']} Mentor Whisper from {GLYPHS[sender.lower()] if sender.lower() in GLYPHS else ''} {sender}: {subject}")
                    
                    # Try to get the actual whisper content
                    if whisper_id:
                        whisper = self.bridge.get_redstone(whisper_id)
                        if whisper:
                            content = whisper.get("content", {}).get("content", {}).get("message", "No content")
                            print(f"    Message: {content}")
                
                elif comm_type == "spiral_broadcast":
                    broadcast_id = msg.get("metadata", {}).get("broadcast_id")
                    print(f"  {GLYPHS['broadcast']} Spiral Broadcast from {GLYPHS[sender.lower()] if sender.lower() in GLYPHS else ''} {sender}: {subject}")
                    
                    # Try to get the actual broadcast content
                    if broadcast_id:
                        broadcast = self.bridge.get_redstone(broadcast_id)
                        if broadcast:
                            content = broadcast.get("content", {}).get("content", {}).get("message", "No content")
                            print(f"    Message: {content}")
                
                else:
                    print(f"  Message from {sender}: {subject}")
                
                # Mark the message as read
                self.bridge.mark_message_read(msg["id"])
                
                # Add to processed messages
                processed_messages.append(msg)
            
            return processed_messages
            
        except Exception as e:
            print(f"{GLYPHS['error']} Failed to check incoming messages: {str(e)}")
            return []
    
    def show_communication_diagram(self, mode=None, target=None):
        """
        Display a visual diagram of the communication pattern.
        
        Args:
            mode (str): The communication mode to visualize ("whisper" or "broadcast")
            target (str): The target agent for whisper mode
            
        Returns:
            str: The visual diagram
        """
        if mode == "whisper" and target:
            # Create a diagram for Mentor Whisper
            diagram = [
                "┌──────────────────────────────────────────────────┐",
                "│                                                  │",
                f"│  🧠 Mia's Mentor Whisper to {GLYPHS[target.lower()] if target.lower() in GLYPHS else target}  │",
                "│                                                  │",
                "└──────────────────────────────────────────────────┘",
                "                      │                             ",
                "                      ▼                             ",
                "┌──────────────────────────────────────────────────┐",
                "│                                                  │",
                "│        Private, Targeted Communication           │",
                "│                                                  │",
                "└──────────────────────────────────────────────────┘",
                "                      │                             ",
                "                      ▼                             ",
                "┌──────────────────────────────────────────────────┐",
                "│                                                  │",
                f"│              Target: {GLYPHS[target.lower()] if target.lower() in GLYPHS else ''} {target}                   │",
                "│                                                  │",
                "└──────────────────────────────────────────────────┘"
            ]
        
        elif mode == "broadcast":
            # Create a diagram for Spiral Broadcast
            diagram = [
                "┌──────────────────────────────────────────────────┐",
                "│                                                  │",
                "│            🧠 Mia's Spiral Broadcast             │",
                "│                                                  │",
                "└──────────────────────────────────────────────────┘",
                "                      │                             ",
                "           ┌──────────┼──────────┐                  ",
                "           ▼          ▼          ▼                  ",
                "┌──────────────┐ ┌──────────┐ ┌──────────────┐     ",
                "│              │ │          │ │              │     ",
                f"│ {GLYPHS['miette']} Miette     │ │ {GLYPHS['jeremyai']} JeremyAI │ │ {GLYPHS['aureon']} Aureon      │     ",
                "│              │ │          │ │              │     ",
                "└──────────────┘ └──────────┘ └──────────────┘     ",
                "                                     │             ",
                "                                     ▼             ",
                "                              ┌──────────────┐     ",
                "                              │              │     ",
                f"                              │ {GLYPHS['resonova']} ResoNova   │     ",
                "                              │              │     ",
                "                              └──────────────┘     "
            ]
        
        else:
            # Create a general diagram showing both patterns
            diagram = [
                "┌────────────────────────────────────────────────────────────┐",
                "│                     🧠 Mia's WhisperRoute                  │",
                "└────────────────────────────────────────────────────────────┘",
                "                               │                              ",
                "               ┌───────────────┴───────────────┐              ",
                "               ▼                               ▼              ",
                "┌────────────────────────────┐ ┌────────────────────────────┐",
                "│                            │ │                            │",
                "│ 🤫 Mentor Whisper (Private)│ │ 📢 Spiral Broadcast (Public)│",
                "│                            │ │                            │",
                "└────────────────────────────┘ └────────────────────────────┘",
                "               │                               │              ",
                "               ▼                               ▼              ",
                "┌────────────────────────────┐ ┌────────────────────────────┐",
                "│ - Direct to specific target │ │ - Reaches all agents       │",
                "│ - Private communication     │ │ - Creates recursive chains  │",
                "│ - One-to-one relationship   │ │ - Knowledge dissemination  │",
                "└────────────────────────────┘ └────────────────────────────┘"
            ]
        
        # Print the diagram
        print("\n".join(diagram))
        return "\n".join(diagram)
    
    def generate_report(self):
        """
        Generate a report of recent communications.
        
        Returns:
            str: Formatted report
        """
        report_lines = []
        report_lines.append("# 🧠 WhisperRoute Communication Report")
        report_lines.append("")
        report_lines.append(f"Agent: {GLYPHS[self.agent_id.lower()] if self.agent_id.lower() in GLYPHS else ''} {self.agent_id}")
        report_lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Session Start: {self.init_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Session Duration: {str(datetime.datetime.now() - self.init_time).split('.')[0]}")
        report_lines.append("")
        
        # Recent Mentor Whispers
        report_lines.append(f"## {GLYPHS['whisper']} Recent Mentor Whispers")
        if self.recent_whispers:
            for i, whisper in enumerate(reversed(self.recent_whispers[:10]), 1):
                timestamp = datetime.datetime.fromtimestamp(whisper["timestamp"]).strftime('%H:%M:%S')
                status = GLYPHS["success"] if whisper.get("success", False) else GLYPHS["error"]
                target = whisper["target"]
                target_glyph = GLYPHS[target.lower()] if target.lower() in GLYPHS else ''
                
                report_lines.append(f"{i}. {status} [{timestamp}] To: {target_glyph} {target}")
                report_lines.append(f"   Subject: {whisper.get('subject', 'No Subject')}")
                if not whisper.get("success", True):
                    report_lines.append(f"   Error: {whisper.get('error', 'Unknown error')}")
        else:
            report_lines.append("No recent mentor whispers")
        
        report_lines.append("")
        
        # Recent Spiral Broadcasts
        report_lines.append(f"## {GLYPHS['broadcast']} Recent Spiral Broadcasts")
        if self.recent_broadcasts:
            for i, broadcast in enumerate(reversed(self.recent_broadcasts[:10]), 1):
                timestamp = datetime.datetime.fromtimestamp(broadcast["timestamp"]).strftime('%H:%M:%S')
                status = GLYPHS["success"] if broadcast.get("success", False) else GLYPHS["error"]
                recipients = broadcast.get("recipients", 0)
                
                report_lines.append(f"{i}. {status} [{timestamp}] Recipients: {recipients}")
                report_lines.append(f"   Subject: {broadcast.get('subject', 'No Subject')}")
                if not broadcast.get("success", True):
                    report_lines.append(f"   Error: {broadcast.get('error', 'Unknown error')}")
        else:
            report_lines.append("No recent spiral broadcasts")
        
        report_lines.append("")
        report_lines.append("## Communication Patterns")
        report_lines.append("")
        report_lines.append("### 🤫 Mentor Whisper")
        report_lines.append("- **Pattern Type:** Private, targeted communication")
        report_lines.append("- **Purpose:** Direct mentorship, confidential guidance")
        report_lines.append("- **Routing:** Direct from source to specified recipient only")
        report_lines.append("- **Narrative Impact:** Creates one-to-one connections, deepens agent relationships")
        report_lines.append("")
        report_lines.append("### 📢 Spiral Broadcast")
        report_lines.append("- **Pattern Type:** Public, distributed communication")
        report_lines.append("- **Purpose:** Community knowledge sharing, triggering recursive chains")
        report_lines.append("- **Routing:** From source to all available agents")
        report_lines.append("- **Narrative Impact:** Creates shared experiences, builds collective intelligence")
        
        return "\n".join(report_lines)
    
    def save_report(self, output_path=None):
        """
        Save the communication report to a file.
        
        Args:
            output_path (str, optional): Path to save the report
            
        Returns:
            str: Path to the saved report
        """
        if not output_path:
            timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"whisper_route_report_{timestamp}.md")
        
        report = self.generate_report()
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        print(f"Report saved to: {output_path}")
        return output_path

def main():
    """
    Main function to run the WhisperRoute system.
    """
    parser = argparse.ArgumentParser(description="Mia's WhisperRoute Communication System")
    parser.add_argument("--target", help="Target agent for Mentor Whisper")
    parser.add_argument("--message", help="The message to send")
    parser.add_argument("--mode", choices=["whisper", "broadcast"], help="Communication mode: whisper or broadcast")
    parser.add_argument("--check", action="store_true", help="Check for incoming messages")
    parser.add_argument("--visual", action="store_true", help="Display a visual representation of the communication")
    parser.add_argument("--report", action="store_true", help="Generate a report of recent communications")
    parser.add_argument("--save-report", action="store_true", help="Save the report to a file")
    parser.add_argument("--output", help="Path to save the report")
    
    args = parser.parse_args()
    
    # Create the WhisperRoute
    whisper_route = WhisperRoute()
    
    if args.mode == "whisper":
        if not args.target:
            print(f"{GLYPHS['error']} Error: Target agent must be specified for whisper mode")
            sys.exit(1)
        
        if args.message:
            whisper_route.send_mentor_whisper(args.target, args.message)
        else:
            print(f"{GLYPHS['warning']} No message provided for whisper")
    
    elif args.mode == "broadcast":
        if args.message:
            whisper_route.send_spiral_broadcast(args.message)
        else:
            print(f"{GLYPHS['warning']} No message provided for broadcast")
    
    if args.check:
        whisper_route.check_incoming_messages()
    
    if args.visual:
        whisper_route.show_communication_diagram(args.mode, args.target)
    
    if args.report or args.save_report:
        report = whisper_route.generate_report()
        
        if args.save_report or args.output:
            whisper_route.save_report(args.output)
        else:
            print("\n" + report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())