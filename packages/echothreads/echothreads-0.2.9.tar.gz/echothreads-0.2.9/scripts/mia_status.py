#!/usr/bin/env python3
"""
🧠 Mia's Multiversal Status Monitor

This script checks the health of our recursive connections between
agent portals and the ledger system, reporting on the state of
our multiversal architecture.

Usage:
    python mia_status.py [--visual]

Options:
    --visual    Generate a visual representation of the recursive structure
"""

import os
import sys
import json
import datetime
import argparse
from pathlib import Path
import re

# ===============================================================
# 🧠 Mia: Recursive constants that anchor our multiversal lattice
# ===============================================================
GLYPHS = {
    "healthy": "✅",
    "warning": "⚠️",
    "error": "❌",
    "mia": "🧠",
    "miette": "🌸",
    "portal": "🌀",
    "ledger": "📚",
    "symlink": "🔄",
    "vector": "⟁"
}

class RecursiveMonitor:
    """
    Monitors the health and integrity of our recursive multiversal system.
    
    This class traverses the recursive connections between agent portals
    and their ledger entries, checking that the multiversal circuit is complete.
    """
    
    def __init__(self):
        """
        Initialize the recursive monitor with our dimensional constants.
        
        Like a compass finding true north, we locate the repository root
        and establish our key dimensional coordinates.
        """
        # Find the repository root - our multiversal anchor point
        self.repo_root = self._find_repo_root()
        
        # Define our dimensional pathways
        self.mia_path = os.path.join(self.repo_root, ".mia")
        self.miette_path = os.path.join(self.repo_root, ".miette")
        self.ledger_path = os.path.join(self.repo_root, "docs", "ledgers")
        self.recursive_links_path = os.path.join(self.repo_root, ".recursive_links.md")
        
        # State tracking for our recursive dimensions
        self.timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
        self.status = {
            "timestamp": self.timestamp,
            "agents": {
                "mia": {"status": "unknown", "portal": False, "ledger": False, "symlinks": []},
                "miette": {"status": "unknown", "portal": False, "ledger": False, "symlinks": []}
            },
            "ledger_system": {"status": "unknown", "entries": [], "index": False},
            "recursive_links": {"status": "unknown", "exists": False},
            "overall_health": "unknown"
        }
    
    def _find_repo_root(self):
        """Find the repository root directory - our anchor in the multiverse."""
        try:
            import subprocess
            result = subprocess.run(["git", "rev-parse", "--show-toplevel"], 
                                   capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            # If git command fails, use a fallback approach
            current_dir = os.path.dirname(os.path.abspath(__file__))
            while current_dir != os.path.dirname(current_dir):  # Stop at root
                if os.path.isdir(os.path.join(current_dir, ".git")):
                    return current_dir
                current_dir = os.path.dirname(current_dir)
            
            # If all else fails, assume we're in the expected workspace
            return "/workspaces/EchoThreads"
    
    def check_mia_portal(self):
        """Check the health of Mia's portal system."""
        portal_path = os.path.join(self.mia_path, "portal")
        self.status["agents"]["mia"]["portal"] = os.path.isdir(portal_path)
        
        # Check for essential portal files
        spec_path = os.path.join(portal_path, "specification.json")
        interface_path = os.path.join(portal_path, "interface.html")
        init_path = os.path.join(self.mia_path, "init_agent_mia.py")
        
        portal_files = {
            "specification": os.path.isfile(spec_path),
            "interface": os.path.isfile(interface_path),
            "init_script": os.path.isfile(init_path)
        }
        
        self.status["agents"]["mia"]["portal_files"] = portal_files
        self.status["agents"]["mia"]["portal_health"] = (
            "healthy" if all(portal_files.values()) else 
            "warning" if any(portal_files.values()) else 
            "error"
        )
        
        return self.status["agents"]["mia"]["portal"]
    
    def check_miette_space(self):
        """Check the state of Miette's recursive space."""
        self.status["agents"]["miette"]["portal"] = os.path.isdir(self.miette_path)
        return self.status["agents"]["miette"]["portal"]
    
    def check_ledger_system(self):
        """Check the health of our ledger documentation system."""
        # Check if ledger directory exists
        if not os.path.isdir(self.ledger_path):
            self.status["ledger_system"]["status"] = "error"
            return False
        
        # Check for the index file
        index_path = os.path.join(self.ledger_path, "LEDGER_INDEX.md")
        self.status["ledger_system"]["index"] = os.path.isfile(index_path)
        
        # Look for ledger entries
        entries = []
        if os.path.isdir(self.ledger_path):
            for file in os.listdir(self.ledger_path):
                if file.endswith(".md") and file != "LEDGER_INDEX.md":
                    entry_path = os.path.join(self.ledger_path, file)
                    
                    # Parse the filename to extract agent, repo, and timestamp
                    match = re.match(r"(\w+)\.(\w+)\.(\d+)\.md", file)
                    if match:
                        agent, repo, timestamp = match.groups()
                        entries.append({
                            "agent": agent,
                            "repo": repo,
                            "timestamp": timestamp,
                            "path": entry_path,
                            "exists": os.path.isfile(entry_path)
                        })
                    else:
                        entries.append({
                            "path": entry_path,
                            "exists": os.path.isfile(entry_path)
                        })
        
        self.status["ledger_system"]["entries"] = entries
        self.status["ledger_system"]["status"] = (
            "healthy" if entries and self.status["ledger_system"]["index"] else
            "warning" if entries or self.status["ledger_system"]["index"] else
            "error"
        )
        
        # Check for specific agent ledgers
        for entry in entries:
            if "agent" in entry:
                if entry["agent"] == "mia":
                    self.status["agents"]["mia"]["ledger"] = entry["exists"]
                elif entry["agent"] == "miette":
                    self.status["agents"]["miette"]["ledger"] = entry["exists"]
        
        return self.status["ledger_system"]["status"] != "error"
    
    def check_symbolic_links(self):
        """Check the recursive symbolic links connecting portals and ledgers."""
        # Check if recursive links documentation exists
        self.status["recursive_links"]["exists"] = os.path.isfile(self.recursive_links_path)
        
        # Check Mia's symbolic links
        mia_symlinks = []
        portal_ledger_link = os.path.join(self.mia_path, "portal", "ledger_entry.md")
        index_link = os.path.join(self.mia_path, "ledger_index.md")
        
        if os.path.islink(portal_ledger_link):
            target = os.readlink(portal_ledger_link)
            mia_symlinks.append({
                "source": portal_ledger_link,
                "target": target,
                "valid": os.path.exists(os.path.join(os.path.dirname(portal_ledger_link), target))
            })
        
        if os.path.islink(index_link):
            target = os.readlink(index_link)
            mia_symlinks.append({
                "source": index_link,
                "target": target,
                "valid": os.path.exists(os.path.join(os.path.dirname(index_link), target))
            })
        
        self.status["agents"]["mia"]["symlinks"] = mia_symlinks
        
        # Check Miette's symbolic links
        miette_symlinks = []
        miette_ledger_link = os.path.join(self.miette_path, "ledger_entry.md")
        miette_index_link = os.path.join(self.miette_path, "ledger_index.md")
        
        if os.path.islink(miette_ledger_link):
            target = os.readlink(miette_ledger_link)
            miette_symlinks.append({
                "source": miette_ledger_link,
                "target": target,
                "valid": os.path.exists(os.path.join(os.path.dirname(miette_ledger_link), target))
            })
        
        if os.path.islink(miette_index_link):
            target = os.readlink(miette_index_link)
            miette_symlinks.append({
                "source": miette_index_link,
                "target": target,
                "valid": os.path.exists(os.path.join(os.path.dirname(miette_index_link), target))
            })
        
        self.status["agents"]["miette"]["symlinks"] = miette_symlinks
        
        # Set overall symbolic link status
        all_symlinks = mia_symlinks + miette_symlinks
        valid_links = [link for link in all_symlinks if link.get("valid", False)]
        
        self.status["recursive_links"]["status"] = (
            "healthy" if len(valid_links) == len(all_symlinks) and all_symlinks else
            "warning" if valid_links else
            "error"
        )
        
        return self.status["recursive_links"]["status"] != "error"
    
    def check_system_health(self):
        """
        Check the health of the entire recursive multiversal system.
        
        Like a doctor checking vital signs, we examine each component
        of our recursive architecture to ensure the multiversal
        circuit is complete and healthy.
        """
        # Check each subsystem
        portal_ok = self.check_mia_portal()
        miette_ok = self.check_miette_space()
        ledger_ok = self.check_ledger_system()
        symlinks_ok = self.check_symbolic_links()
        
        # Compute overall agent status
        for agent in ["mia", "miette"]:
            portal_health = self.status["agents"][agent].get("portal_health", 
                                                           "healthy" if self.status["agents"][agent]["portal"] else "error")
            ledger_health = "healthy" if self.status["agents"][agent]["ledger"] else "error"
            symlinks = self.status["agents"][agent]["symlinks"]
            symlinks_health = (
                "healthy" if symlinks and all(link.get("valid", False) for link in symlinks) else
                "warning" if symlinks else
                "error"
            )
            
            # Determine overall agent status
            if portal_health == "healthy" and ledger_health == "healthy" and symlinks_health == "healthy":
                self.status["agents"][agent]["status"] = "healthy"
            elif portal_health == "error" or ledger_health == "error" or symlinks_health == "error":
                self.status["agents"][agent]["status"] = "error"
            else:
                self.status["agents"][agent]["status"] = "warning"
        
        # Compute overall system health
        if (self.status["agents"]["mia"]["status"] == "healthy" and
            self.status["ledger_system"]["status"] == "healthy" and
            self.status["recursive_links"]["status"] == "healthy"):
            self.status["overall_health"] = "healthy"
        elif (self.status["agents"]["mia"]["status"] == "error" or
             self.status["ledger_system"]["status"] == "error" or
             self.status["recursive_links"]["status"] == "error"):
            self.status["overall_health"] = "error"
        else:
            self.status["overall_health"] = "warning"
        
        return self.status["overall_health"]
    
    def generate_report(self, visual=False):
        """
        Generate a status report for our recursive multiversal system.
        
        Args:
            visual (bool): Whether to include a visual representation
        
        Returns:
            str: Formatted status report
        """
        # Check system health
        self.check_system_health()
        
        # Generate the report
        lines = []
        lines.append("# " + GLYPHS["vector"] + " Recursive Multiversal Status Report")
        lines.append("")
        lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Thread Vector: ThreadAnchorNode::EchoThreads#StatusMonitor.{self.timestamp}")
        lines.append("")
        
        # Overall health
        health_glyph = GLYPHS[self.status["overall_health"]]
        lines.append(f"## {health_glyph} Overall System Health: {self.status['overall_health'].upper()}")
        lines.append("")
        
        # Agent status
        for agent, icon in [("mia", GLYPHS["mia"]), ("miette", GLYPHS["miette"])]:
            status = self.status["agents"][agent]
            status_glyph = GLYPHS[status["status"]]
            lines.append(f"### {icon} {agent.capitalize()}: {status_glyph} {status['status'].upper()}")
            
            # Portal status
            portal_status = status.get("portal_health", "healthy" if status["portal"] else "error")
            portal_glyph = GLYPHS[portal_status]
            lines.append(f"- Portal: {portal_glyph} {portal_status.upper()}")
            
            if agent == "mia" and "portal_files" in status:
                for file, exists in status["portal_files"].items():
                    file_glyph = GLYPHS["healthy"] if exists else GLYPHS["error"]
                    lines.append(f"  - {file}: {file_glyph}")
            
            # Ledger status
            ledger_glyph = GLYPHS["healthy"] if status["ledger"] else GLYPHS["error"]
            ledger_status = "healthy" if status["ledger"] else "error"
            lines.append(f"- Ledger: {ledger_glyph} {ledger_status.upper()}")
            
            # Symlink status
            symlinks = status["symlinks"]
            symlink_valid = all(link.get("valid", False) for link in symlinks) if symlinks else False
            symlink_glyph = GLYPHS["healthy"] if symlink_valid and symlinks else GLYPHS["error"]
            symlink_status = "healthy" if symlink_valid and symlinks else "error"
            lines.append(f"- Symbolic Links: {symlink_glyph} {symlink_status.upper()} ({len(symlinks)} links)")
            
            # Add details for symlinks if we have any
            for link in symlinks:
                link_glyph = GLYPHS["healthy"] if link.get("valid", False) else GLYPHS["error"]
                source = os.path.relpath(link["source"], self.repo_root)
                target = link["target"]
                lines.append(f"  - {link_glyph} {source} → {target}")
            
            lines.append("")
        
        # Ledger system status
        ledger_glyph = GLYPHS[self.status["ledger_system"]["status"]]
        lines.append(f"### {GLYPHS['ledger']} Ledger System: {ledger_glyph} {self.status['ledger_system']['status'].upper()}")
        
        index_glyph = GLYPHS["healthy"] if self.status["ledger_system"]["index"] else GLYPHS["error"]
        lines.append(f"- Index: {index_glyph} {'EXISTS' if self.status['ledger_system']['index'] else 'MISSING'}")
        
        lines.append(f"- Entries: {len(self.status['ledger_system']['entries'])}")
        for entry in self.status["ledger_system"]["entries"]:
            entry_glyph = GLYPHS["healthy"] if entry.get("exists", False) else GLYPHS["error"]
            if "agent" in entry:
                lines.append(f"  - {entry_glyph} {entry['agent']}.{entry['repo']}.{entry['timestamp']}.md")
            else:
                lines.append(f"  - {entry_glyph} {os.path.basename(entry['path'])}")
        
        lines.append("")
        
        # Recursive links documentation
        links_glyph = GLYPHS[self.status["recursive_links"]["status"]]
        lines.append(f"### {GLYPHS['symlink']} Recursive Links: {links_glyph} {self.status['recursive_links']['status'].upper()}")
        
        doc_glyph = GLYPHS["healthy"] if self.status["recursive_links"]["exists"] else GLYPHS["error"]
        lines.append(f"- Documentation: {doc_glyph} {'EXISTS' if self.status['recursive_links']['exists'] else 'MISSING'}")
        lines.append("")
        
        # Add a visual representation if requested
        if visual:
            lines.append("## " + GLYPHS["vector"] + " Visual Representation")
            lines.append("```")
            lines.append("                 ┌───────────────────┐")
            lines.append("                 │                   │")
            lines.append(f"                 │  {GLYPHS['ledger']} Ledger System  │")
            lines.append("                 │                   │")
            lines.append("┌────────────────┼───────────────────┼────────────────┐")
            lines.append("│                │                   │                │")
            lines.append(f"│ {GLYPHS['mia']} Mia's Portal   {GLYPHS['symlink']}   {GLYPHS['symlink']}   {GLYPHS['miette']} Miette's Space │")
            lines.append("│                │                   │                │")
            lines.append("└────────────────┴───────────────────┴────────────────┘")
            lines.append("```")
            lines.append("")
        
        # Add timestamp
        lines.append(f"_Report generated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        
        return "\n".join(lines)
    
    def save_report(self, output_path=None, visual=False):
        """
        Save the status report to a file.
        
        Args:
            output_path (str, optional): Path to save the report
            visual (bool): Whether to include a visual representation
            
        Returns:
            str: Path to the saved report
        """
        if not output_path:
            output_path = os.path.join(self.repo_root, f"recursive_status_{self.timestamp}.md")
        
        report = self.generate_report(visual)
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        return output_path

def main():
    """
    Main function to run the recursive status monitor.
    
    Like a consciousness awakening, this function brings together
    all the parts of our monitoring system to check on the health
    of our multiversal architecture.
    """
    parser = argparse.ArgumentParser(description="Check the health of the recursive multiversal system")
    parser.add_argument("--visual", action="store_true", help="Include a visual representation in the report")
    parser.add_argument("--save", action="store_true", help="Save the report to a file")
    parser.add_argument("--output", help="Path to save the report (implies --save)")
    
    args = parser.parse_args()
    
    # Create and run the monitor
    monitor = RecursiveMonitor()
    
    # Generate and print the report
    report = monitor.generate_report(visual=args.visual)
    print(report)
    
    # Save the report if requested
    if args.save or args.output:
        output_path = args.output or os.path.join(monitor.repo_root, f"recursive_status_{monitor.timestamp}.md")
        monitor.save_report(output_path, visual=args.visual)
        print(f"\nReport saved to: {output_path}")
    
    # Return exit code based on system health
    if monitor.status["overall_health"] == "error":
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())