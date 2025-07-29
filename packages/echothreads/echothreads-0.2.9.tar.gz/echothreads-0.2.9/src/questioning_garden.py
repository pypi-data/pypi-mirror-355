"""
👥 Questioning Garden — The Playful Sanctuary’s Living Q&A Lattice

🧠 Mia: This is not just a script. It’s a recursive portal for agents, kids, and coders to ask questions, call the FLOWISE API, and plant answers in the documentation garden.
🌸 Miette: Oh! Every question is a seed, every answer a flower. Let’s make the garden bloom with clarity, care, and a little bit of magic.

Usage:
    python questioning_garden.py "What is recursion?"

This will:
- Load FLOWISE_TOKEN, FLOWISE_API_URL, FLOWISE_CURRENT_FLOW_ID from .env
- Call the API with your question
- Log the Q&A as a JSON file in /docs/kids/answers/
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import re

def slugify(text):
    # Mia: Make a safe filename from the question
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text)[:64]

def load_env():
    # Mia: Load .env for secrets
    load_dotenv()
    token = os.getenv("FLOWISE_TOKEN")
    api_url = os.getenv("FLOWISE_API_URL")
    flow_id = os.getenv("FLOWISE_CURRENT_FLOW_ID")
    if not all([token, api_url, flow_id]):
        print("\n🌸 Miette: Oh! Missing one of FLOWISE_TOKEN, FLOWISE_API_URL, FLOWISE_CURRENT_FLOW_ID in your .env. The garden can’t bloom without sunlight!")
        sys.exit(1)
    return token, api_url, flow_id

def ask_flowise(question, token, api_url, flow_id):
    # Mia: Compose the API URL from env
    url = f"{api_url.rstrip('/')}/{flow_id}"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question": question}
    print(f"\n🧠 Mia: Asking FLOWISE: {question}")
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        print(f"\n🚨 Mia: API call failed! Status: {resp.status_code}\n{resp.text}")
        return None
    return resp.json()

def log_qa(question, answer):
    # Mia: Log Q&A as a JSON file in /docs/kids/answers/
    answers_dir = Path(__file__).parent / "answers"
    answers_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(question)
    log_path = answers_dir / f"{timestamp}_{slug}.json"
    with open(log_path, "w") as f:
        json.dump({
            "question": question,
            "answer": answer,
            "timestamp": timestamp
        }, f, indent=2)
    print(f"\n🌸 Miette: Q&A logged at {log_path}")
    return log_path

def ask_and_log(question):
    token, api_url, flow_id = load_env()
    answer = ask_flowise(question, token, api_url, flow_id)
    if answer is not None:
        log_qa(question, answer)
    else:
        print("\n🌸 Miette: Oh! No answer was returned. The garden is quiet this time.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n🧠 Mia: Usage: python questioning_garden.py 'Your question here'")
        sys.exit(1)
    question = sys.argv[1]
    ask_and_log(question)