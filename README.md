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

# Place-holder-name
A game coded by Armia Mousavian. Graphics by Dion Brown, Story and design by Vincent Cabrera.

How to use this:
Above are the files for this project.
If you click on the you can view the code and change it.
After changing anything you must commit witch then will requare my permission to be added to the main thing.
You can add tips and how to play this in the wiki tab.
You can only run this on a pc with python installed (can change later but then we can not edit it).
/n
New ideas or comments or changes or tips in the discussions tab please.
Dion, Don't go crazy.
- Create issues for the multiplayer, UI, and persistence work and assign them to you/Dion/Vincent.
- Expand the server into a more robust authoritative server with tickrate and action reconciliation.
