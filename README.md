# Dungeon: Placeholder Name (extended)

This repo contains a dungeon roguelike prototype (Python) with:
- 50-level design idea (configurable).
- Shop and crystals progression.
- Persistence with offline (local JSON) profiles and optional online accounts.
- Pygame GUI skeleton for demo and editing of graphics.
- Simple multiplayer with an authoritative TCP server (supports up to 3 players); mobs scale with player count.

Requirements
- Python 3.8+
- Optional: pygame (`pip install pygame`)
- Optional: requests (`pip install requests`) for online account features

Quick start (local single-player demo)
- Install optional deps (recommended):
  pip install pygame requests
- Run the GUI:
  python -m dungeon_game.main
  Choose "Start Local Game" to run a GUI demo.

Start multiplayer server (simple local server)
- Run the server in a terminal:
  python -m dungeon_game.server
- In the GUI, choose "Connect to Server" and provide host (default localhost) and port (default 6000).
- Up to 3 players can join; mobs will be scaled automatically by amount of connected players.

Persistence
- Local profiles are stored in: ~/.dungeon_game/profiles/<name>.json
- The OnlineAuthClient is a client for an online endpoint (not included). If no server is available, the GUI will fallback to local-only profiles.

Files added/modified
- src/dungeon_game/persistence.py  -- local + optional online account client
- src/dungeon_game/network.py      -- simple JSON-over-TCP client helper
- src/dungeon_game/server.py       -- small threaded authoritative server
- src/dungeon_game/gui.py          -- Pygame GUI skeleton (editable art)
- src/dungeon_game/multiplayer.py  -- server-side orchestrator + helper functions
- src/dungeon_game/level.py        -- updated to scale mobs by player count
- src/dungeon_game/game.py         -- updated run_level accepts player_count, multiplayer-friendly
- src/dungeon_game/main.py         -- launcher updated to choose GUI/Server/CLI

Notes
- The provided networking/server code is a minimal prototype. For public internet play, you'll want to add authentication, encryption (TLS), and handle NAT/port forwarding or run a hosted server.
- The GUI uses simple placeholders for graphics so you can swap in your sprites.

If you want, I can:
- Push these changes to a branch in armiagithub/Place-holder-name.
- Create issues for the multiplayer, UI, and persistence work and assign them to you/Dion/Vincent.
- Expand the server into a more robust authoritative server with tickrate and action reconciliation.
