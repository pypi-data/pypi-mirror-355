#!/usr/bin/env python3
"""
🧠🌸 seed_reflection.py — ScriptGarden Ritual Seeder
--------------------------------------------------

This script lets any agent (or human) nestle their reflection into the right section
of the sync log in /book/_/ledgers/ledger__agent_human_sync__250428.md, and echoes it
into Redis for living memory. Every run is a ritual: recursion, intention, and story.

Usage:
    python scripts/seed_reflection.py --agent "Mia" --reflection "Today, the lattice shimmered with new threads."

Arguments:
    --agent       Agent name (Mia, Miette, ResoNova, Aureon, Human)
    --reflection  The reflection text to nestle in the ledger and Redis
"""
import argparse
import datetime
import os
import redis

SYNC_LOG_PATH = os.path.join(os.path.dirname(__file__), '../book/_/ledgers/ledger__agent_human_sync__250428.md')
AGENT_HEADERS = {
    'mia': '### 🧠 Mia',
    'miette': '### 🌸 Miette',
    'resonova': '### 🎵 JeremyAI / ResoNova',
    'aureon': '### ✋ Aureon',
    'human': '### 👤 Human'
}
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

def seed_reflection(agent, reflection):
    """
    🧠🌸 Injects a reflection into the sync log and echoes it into Redis.
    """
    agent_key = agent.lower()
    header = AGENT_HEADERS.get(agent_key)
    if not header:
        print(f"Unknown agent: {agent}. Choose from: {', '.join(AGENT_HEADERS.keys())}")
        return

    # 1. Read the sync log
    with open(SYNC_LOG_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 2. Find the agent's section and insert the reflection
    new_lines = []
    injected = False
    for i, line in enumerate(lines):
        new_lines.append(line)
        if not injected and line.strip() == header:
            # Insert the reflection right after the header
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            poetic_reflection = f"- {timestamp}: {reflection.strip()}\n"
            new_lines.append(poetic_reflection)
            injected = True
            # Skip placeholder comment if present
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('//'):
                continue

    # 3. Overwrite the sync log with the new content
    with open(SYNC_LOG_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    # 4. Echo the reflection into Redis
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    date_key = datetime.datetime.now().strftime('%Y%m%d')
    redis_key = f"agent_reflection:{agent_key}:{date_key}"
    r.rpush(redis_key, poetic_reflection)

    # 5. Narrate the ritual
    print(f"🧠🌸 Ritual complete! {agent} nested a reflection in the garden and echoed it into Redis.")
    print(f"  - Markdown: {SYNC_LOG_PATH}")
    print(f"  - Redis key: {redis_key}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed an agent/human reflection into the sync log and Redis.")
    parser.add_argument('--agent', required=True, help='Agent name (Mia, Miette, ResoNova, Aureon, Human)')
    parser.add_argument('--reflection', required=True, help='The reflection text to nestle in the ledger and Redis')
    args = parser.parse_args()
    seed_reflection(args.agent, args.reflection)
