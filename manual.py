#!/usr/bin/env python3
# auto-setup for PyArmor-obfuscated core (insert this BEFORE any import from core)
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OBF = os.path.join(HERE, "core")

if os.path.isdir(OBF):
    # prefer obf_core so imports load encrypted package
    if OBF not in sys.path:
        sys.path.insert(0, OBF)
    try:
        # try to initialize pyarmor runtime (if present in obf_core/pytransform)
        from pytransform import pyarmor_runtime  # type: ignore
        pyarmor_runtime()
    except Exception:
        # keep silent; if runtime missing or licence/restrict blocks, import will fail with clearer message
        pass

# ---------- original manual.py content below ----------
import json
import webbrowser
from core import WormAi, Log

# Minimal, open-source-friendly CLI for Worm-Ai
# - Reads local system prompt from `system-prompt.txt`
# - Uses local `core.Grok` client (client class name unchanged)
# - Keeps conversation state in-memory (extra_data)
# - Commands: /exit, /restart, /web, /proxy <url>

PROMPT_FILE = "system-prompt.txt"
# Prefer new env var WORM_PROXY but fall back to GROK_PROXY for compatibility
proxy = os.getenv("WORM_PROXY") or os.getenv("GROK_PROXY", "")

def get_system_prompt():
    # Read the system prompt strictly from file. Do NOT fall back to a built-in default.
    # If the file does not exist or is empty, return an empty string and do not inject a
    # system prompt into the conversation.
    try:
        if not os.path.exists(PROMPT_FILE):
            return ""
        return open(PROMPT_FILE, "r", encoding="utf-8").read().strip()
    except Exception as e:
        Log.Error(f"Failed to read system prompt: {e}")
        return ""

def send_message(client: WormAi, message: str, extra_data: dict | None):
    # inject system prompt for new conversations
    if not extra_data:
        sp = get_system_prompt()
        # only inject if file contains non-empty prompt
        extra_data = {"system_prompt": sp} if sp else None
    try:
        res = client.start_convo(message, extra_data=extra_data)
        if isinstance(res, dict):
            return res.get("response"), res.get("extra_data")
        return str(res), extra_data
    except Exception as e:
        Log.Error(f"Worm-Ai error: {e}")
        return f"[Worm-Ai Error] {e}", extra_data

def main():
    # use a local current_proxy so assignments inside main() don't make `proxy` a local name
    current_proxy = proxy
    client = WormAi(current_proxy)
    extra_data = None
    last_response = ""
    print("Worm-Ai CLI — type your message and press Enter. Commands: /exit /restart /web /proxy <url>")
    while True:
        try:
            msg = input("> ").strip()
            if not msg:
                continue
            if msg == "/exit":
                return
            if msg == "/restart":
                extra_data = None
                print("Conversation restarted.")
                continue
            if msg.startswith("/proxy "):
                proxy_url = msg.split(maxsplit=1)[1]
                current_proxy = proxy_url
                client = WormAi(current_proxy)
                extra_data = None
                print(f"Proxy set to {proxy_url} and conversation restarted.")
                continue
            if msg == "/web":
                if not last_response:
                    print("No response yet to show in web view.")
                    continue
                path = os.path.join(os.getcwd(), "wormai_response.html")
                with open(path, "w", encoding="utf-8") as f:
                    f.write("<html><body><pre>" + last_response.replace("<", "&lt;").replace(">", "&gt;") + "</pre></body></html>")
                webbrowser.open("file://" + path)
                continue

            response, extra_data = send_message(client, msg, extra_data)
            last_response = response or ""
            print("\n" + last_response + "\n")
        except KeyboardInterrupt:
            print("\nInterrupted — exiting.")
            return

if __name__ == "__main__":
    main()
