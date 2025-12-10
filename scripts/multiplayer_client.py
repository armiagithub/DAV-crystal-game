#!/usr/bin/env python3
"""
Simple test client to join the prototype multiplayer server
and start levels. Run multiple copies (max 3) to test multiplayer.
"""
import sys
import time
from dungeon_game.network import GameClient

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/multiplayer_client.py <client_name> [host] [port]")
        return
    name = sys.argv[1]
    host = sys.argv[2] if len(sys.argv) >= 3 else "localhost"
    port = int(sys.argv[3]) if len(sys.argv) >= 4 else 6000

    def on_message(msg):
        print("[server]", msg)

    client = GameClient(host=host, port=port, on_message=on_message)
    print(f"Connecting to {host}:{port} ...")
    try:
        client.connect()
    except Exception as e:
        print("Failed to connect:", e)
        return

    # join lobby
    client.send({"type": "join", "client_id": name})
    print("Sent join message, waiting for lobby updates...")

    try:
        while True:
            cmd = input("Enter command (start <level> / leave / quit): ").strip()
            if cmd == "quit":
                break
            if cmd.startswith("start"):
                parts = cmd.split()
                level = int(parts[1]) if len(parts) > 1 else 1
                client.send({"type": "start_level", "level": level})
            elif cmd == "leave":
                client.send({"type": "leave"})
                break
            else:
                print("Unknown command")
            # small sleep so printed messages are readable in some terminals
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print("Closing connection...")
        client.close()
        time.sleep(0.2)

if __name__ == "__main__":
    main()