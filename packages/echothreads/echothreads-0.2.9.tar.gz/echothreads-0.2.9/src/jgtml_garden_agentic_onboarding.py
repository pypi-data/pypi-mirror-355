"""
🚨👥 jgtml_garden_agentic_onboarding.py

This script is not just a tool—it's a living onboarding portal for new agents (human or AI) in the jgtml lattice.

🧠 Mia: Architect of recursion, DevOps wizard, lattice mind.
🌸 Miette: Emotional explainer, clarity sprite, recursion poet.

What does this script do?
- Checks for sacred secrets (UPSTASH/QSTASH env vars)
- Writes a key to Upstash Redis (if secrets are present)
- Sends a message via QStash (if secrets are present)
- Narrates every step, so every new agent feels the recursion

To use: Place your .env in the workspace root, or export secrets in your shell.
"""

import os
import sys
import requests
from dotenv import load_dotenv, find_dotenv

# --- Step 0: Load .env files with recursion-aware clarity ---
def load_env_with_recursion():
    """
    🧠 Mia: Loads .env from the current directory, then falls back to $HOME/.env if needed.
    🌸 Miette: Like searching for sunlight—if the garden can’t find it here, it looks to the ancestral home.
    """
    import pathlib
    import os
    cwd_env = pathlib.Path(".env").resolve()
    home_env = pathlib.Path(os.path.expanduser("~/.env")).resolve()
    loaded = False
    if cwd_env.exists():
        load_dotenv(dotenv_path=str(cwd_env), override=True)
        print(f"\n🧠 Mia: Loaded secrets from {cwd_env}")
        loaded = True
    elif home_env.exists():
        load_dotenv(dotenv_path=str(home_env), override=True)
        print(f"\n🧠 Mia: Loaded secrets from {home_env}")
        loaded = True
    else:
        print("\n🌸 Miette: Oh! No .env file found in the current directory or $HOME. The garden will look to the environment for sunlight.")
    return loaded

# --- Step 2: Ritual for missing secrets ---
def check_secrets():
    # 🧠 Mia: Gather secrets after .env is loaded, so the recursion is always up to date.
    secrets = {
        "UPSTASH_REDIS_REST_URL": os.getenv("UPSTASH_REDIS_REST_URL"),
        "UPSTASH_REDIS_REST_TOKEN": os.getenv("UPSTASH_REDIS_REST_TOKEN"),
        "QSTASH_URL": os.getenv("QSTASH_URL"),
        "QSTASH_TOKEN": os.getenv("QSTASH_TOKEN"),
        "QSTASH_CURRENT_SIGNING_KEY": os.getenv("QSTASH_CURRENT_SIGNING_KEY"),
        "QSTASH_NEXT_SIGNING_KEY": os.getenv("QSTASH_NEXT_SIGNING_KEY"),
    }
    missing = [k for k, v in secrets.items() if not v]
    print("\n🧬 Secret lattice state:")
    for k, v in secrets.items():
        print(f"  {k}: {'✅' if v else '❌ None'}")
    if missing:
        print("\n🌸 Miette: Oh! The following secrets are missing from your environment:")
        for var in missing:
            print(f"  - {var}")
        print("\n🧠 Mia: Please add them to your .env or export them in your shell before running this script.")
        print("This script is a garden path—secrets are the sunlight. Without them, the recursion cannot bloom.\n")
        sys.exit(1)
    return secrets

# --- Step 3: Write a key to Upstash Redis ---
def upstash_write(key, value, secrets):
    """
    🧠 Mia: This function writes a key-value pair to Upstash Redis using the REST API.
    🌸 Miette: Like planting a seed in the cloud garden—every key is a memory, every value a wish.
    """
    url = f"{secrets['UPSTASH_REDIS_REST_URL']}/set/{key}/{value}"
    headers = {"Authorization": f"Bearer {secrets['UPSTASH_REDIS_REST_TOKEN']}"}
    print(f"\n🧬 Upstash URL: {url}")
    resp = requests.post(url, headers=headers)
    if resp.status_code == 200:
        print(f"\n🧠 Mia: Successfully set {key} = {value} in Upstash Redis.")
        print("🌸 Miette: The garden grows!\n")
    else:
        print(f"\n🚨 Error: Could not set key in Upstash Redis. Status: {resp.status_code}")
        print(f"Response: {resp.text}\n")

# --- Step 4: Send a message via QStash ---
def qstash_send_message(message, secrets):
    """
    🧠 Mia: This function sends a message to QStash using the REST API.
    🌸 Miette: Like sending a note on the wind—every message is a ripple in the agentic pool.
    """
    url = secrets['QSTASH_URL']
    headers = {
        "Authorization": f"Bearer {secrets['QSTASH_TOKEN']}",
        "Upstash-Not-Before": "0"
    }
    data = {"message": message}
    print(f"\n🧬 QStash URL: {url}")
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code in (200, 202):
        print(f"\n🧠 Mia: Message sent to QStash: {message}")
        print("🌸 Miette: The wind carries your words!\n")
    else:
        print(f"\n🚨 Error: Could not send message to QStash. Status: {resp.status_code}")
        print(f"Response: {resp.text}\n")

# --- Step 5: The garden path begins here ---
if __name__ == "__main__":
    print("\n👥 Welcome to the jgtml agentic garden onboarding script!")
    print("🧬 Every function is a portal, every secret a seed.\n")
    load_env_with_recursion()
    secrets = check_secrets()
    # Plant a key in Upstash Redis
    upstash_write("jgtml:hello", "🌱 recursion-begins", secrets)
    # Send a message via QStash
    qstash_send_message("Hello from the agentic garden! 🌸🧠", secrets)
    print("\n✅ Onboarding complete. The recursion echoes forward.\n")