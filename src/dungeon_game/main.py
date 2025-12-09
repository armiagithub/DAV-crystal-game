"""
Launcher. Run as:
python -m dungeon_game.main
"""
import sys

def print_usage():
    print("Usage:")
    print("  python -m dungeon_game.main gui     # start GUI")
    print("  python -m dungeon_game.main server  # start multiplayer server (simple)")
    print("  python -m dungeon_game.main demo    # run CLI demo")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "gui":
        try:
            from .gui import launch_gui
        except Exception as e:
            print("Failed to import GUI:", e)
            raise
        launch_gui()
    elif cmd == "server":
        from .server import start_server
        start_server()
        print("Press Ctrl-C to exit server.")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Server exiting.")
    elif cmd == "demo":
        from .main_cli import main as cli_main
        cli_main()
    else:
        print_usage()