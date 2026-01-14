"""
Launcher. Run as:
python -m dungeon_game.main
"""
import sys
import importlib
import traceback

def print_usage():
    print("Usage:")
    print("  python -m dungeon_game.main gui     # start GUI")
    print("  python -m dungeon_game.main server  # start multiplayer server (simple)")
    print("  python -m dungeon_game.demo    # run CLI demo")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "gui":
        try:
            # Import the gui module dynamically so we can provide better diagnostics
            gui_mod = importlib.import_module(f"{__package__}.gui")
        except Exception:
            print("Failed to import GUI module; full traceback follows:")
            traceback.print_exc()
            raise
        # Ensure the symbol exists and is callable
        try:
            launch_gui = getattr(gui_mod, "launch_gui")
        except AttributeError:
            print(f"Module loaded from: {getattr(gui_mod, '__file__', '<unknown>')}")
            print("Available names in the module:")
            names = [n for n in dir(gui_mod) if not n.startswith("_")]
            print(names)
            raise ImportError("'launch_gui' not found in dungeon_game.gui; see available names above")
        # Call the launcher
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
