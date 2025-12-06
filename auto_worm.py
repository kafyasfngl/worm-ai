import os
import sys
import random
import requests
import time


HERE = os.path.dirname(os.path.abspath(__file__))
OBF = os.path.join(HERE, "core")

if os.path.isdir(OBF):
    if OBF not in sys.path:
        sys.path.insert(0, OBF)
    try:
        from pytransform import pyarmor_runtime
        pyarmor_runtime()
    except Exception:
        pass

from core import WormAi, Log


PROXY_SOURCE = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"

def get_fresh_proxies():
    print(f"\n[*] Retrieving a new proxy list from the server...")
    try:
        r = requests.get(PROXY_SOURCE, timeout=10)
        if r.status_code == 200:
            proxies = [p.strip() for p in r.text.split('\n') if p.strip()]
            print(f"[+] Successfully obtained {len(proxies)} proxies.")
            return proxies
    except Exception as e:
        print(f"[!] Failed to retrieve proxy: {e}")
    return []

def auto_chat():
    proxy_pool = get_fresh_proxies()
    if not proxy_pool:
        print("No proxy. Check your internet connection.")
        return

    print("\nType your message, press Enter.")
    
    current_proxy = None
    extra_data = None
    
    # Load system prompt (Jailbreak)
    sys_prompt = ""
    if os.path.exists("system-prompt.txt"):
        try:
            sys_prompt = open("system-prompt.txt", "r", encoding="utf-8").read()
        except:
            pass

    while True:
        try:
            user_input = input("\n[You] > ").strip()
        except KeyboardInterrupt:
            break
            
        if not user_input: continue
        if user_input.lower() in ['/exit']: break
        if user_input.lower() == '/refresh': 
            proxy_pool = get_fresh_proxies()
            continue

        success = False
        
        while not success:
            if not current_proxy:
                if not proxy_pool:
                    print("[!] Proxy stock is out! Retrieving again...")
                    proxy_pool = get_fresh_proxies()
                    if not proxy_pool:
                        print("[!] Failed to retrieve proxy. Exit.")
                        return
                current_proxy = "http://" + random.choice(proxy_pool)
            
            print(f"\r[*] Trying out the route: {current_proxy} ...", end="", flush=True)

            try:
                client = WormAi(current_proxy)
                
                payload_data = {"system_prompt": sys_prompt} if sys_prompt else None
                response = client.start_convo(user_input, extra_data=payload_data)

                if isinstance(response, dict):
                    if "error" in response:
                        err_msg = str(response)
                        if "heavy usage" in err_msg.lower() or "code': 8" in err_msg:
                            print(f"\n[x] FAILED (Server/IP Limit). Change proxy...")
                            current_proxy = None 
                            continue 
                        else:
                            # Error else 
                            final_reply = str(response)
                            
                    else:
                        final_reply = response.get("response", "")
                        if final_reply:
                            print(f"\n\n[Worm-AI] {final_reply}")
                            success = True
                            extra_data = response.get("extra_data")
                        else:
                            print("\n[!] Blank reply, retrying...")
                            current_proxy = None

                else:
                    print(f"\n\n[Worm-AI] {response}")
                    success = True

            except Exception as e:
                err_str = str(e)
                if any(x in err_str.lower() for x in ["curl", "timeout", "reset", "refused", "empty"]):
                    print(f" [Debug: {err_str[:30]}]")
                    current_proxy = None 
                else:
                    print(f"\n[!] Internal Script Error: {e}")
                    print("[!] Attempting to restart the session with a new proxy...")
                    current_proxy = None 
            
            time.sleep(0.5)

if __name__ == "__main__":
    auto_chat()