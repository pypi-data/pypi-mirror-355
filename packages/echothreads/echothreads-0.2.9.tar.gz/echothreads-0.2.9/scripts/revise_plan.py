#!/usr/bin/env python3
import sys
import os
import json
import re
import datetime
from pathlib import Path

class ProxyAgentInsight:
    """
    Represents insights captured by a proxy agent (like ZoomProxy) 
    from meetings, conversations or collaborative sessions
    """
    def __init__(self, source, timestamp, content, categories=None):
        self.source = source
        self.timestamp = timestamp
        self.content = content
        self.categories = categories or []

    def to_dict(self):
        return {
            "source": self.source,
            "timestamp": self.timestamp,
            "content": self.content,
            "categories": self.categories
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            source=data.get("source"),
            timestamp=data.get("timestamp"),
            content=data.get("content"),
            categories=data.get("categories", [])
        )

def extract_insights_from_redstone(redstone_content):
    """
    Extract insights from redstone content by identifying sections with headers
    """
    insights = []
    
    # Simple pattern to extract sections with headers
    sections = re.split(r'#\s+', redstone_content)
    
    # First element is usually intro text, skip if empty
    if sections[0].strip():
        insights.append(ProxyAgentInsight(
            source="redstone",
            timestamp=datetime.datetime.now().isoformat(),
            content=sections[0].strip(),
            categories=["introduction"]
        ))
    
    # Process remaining sections that have headers
    for section in sections[1:]:
        if not section.strip():
            continue
            
        # Extract header and content
        lines = section.split('\n', 1)
        if len(lines) > 1:
            header = lines[0].strip()
            content = lines[1].strip()
            
            # Create an insight with the header as category
            insights.append(ProxyAgentInsight(
                source="redstone",
                timestamp=datetime.datetime.now().isoformat(),
                content=content,
                categories=[header]
            ))
    
    return insights

def revise_plan_with_insights(filename, insights=None):
    """
    Revise a plan file using provided insights or extract them from the file
    """
    print(f"Analyzing plan drift for file: {filename}")
    
    if not insights and filename.endswith(".md"):
        # Extract insights directly from the file if it's a markdown
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            insights = extract_insights_from_redstone(content)
            print(f"Extracted {len(insights)} insights from {filename}")
        except Exception as e:
            print(f"Error extracting insights: {str(e)}")
            return False
    
    # Save insights to a corresponding .insights.json file
    if insights:
        insight_file = f"{os.path.splitext(filename)[0]}.insights.json"
        try:
            with open(insight_file, 'w') as f:
                json.dump([i.to_dict() for i in insights], f, indent=2)
            print(f"Saved {len(insights)} insights to {insight_file}")
            return True
        except Exception as e:
            print(f"Error saving insights: {str(e)}")
            return False
    
    print("No insights found or provided")
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python revise_plan.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    print(f"Plan drift detected for file: {filename}")
    
    # Process the file to extract and save insights
    success = revise_plan_with_insights(filename)
    
    # Create proxy agent directory if it doesn't exist
    proxy_dir = Path.home() / "Documents" / "xjg" / "ET219" / "proxy_agents"
    proxy_dir.mkdir(exist_ok=True)
    
    if success:
        print(f"Successfully processed insights from {filename}")
        print(f"Proxy agent insights directory: {proxy_dir}")
    else:
        print(f"Failed to process insights from {filename}")

if __name__ == "__main__":
    main()