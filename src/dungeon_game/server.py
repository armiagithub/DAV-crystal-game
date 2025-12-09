import socketserver
import threading
import json
from typing import Dict, List
from .level import Level

MAX_PLAYERS = 3


class LobbyState:
    def __init__(self):
        self.lock = threading.Lock()
        self.clients: Dict[str, "RequestHandler"] = {}  # client_id -> handler

    def add(self, client_id: str, handler: "RequestHandler") -> bool:
        with self.lock:
            if len(self.clients) >= MAX_PLAYERS:
                return False
            self.clients[client_id] = handler
            return True

    def remove(self, client_id: str):
        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]

    def list_clients(self) -> List[str]:
        with self.lock:
            return list(self.clients.keys())

    def broadcast(self, message: Dict):
        with self.lock:
            for handler in list(self.clients.values()):
                try:
                    handler.send_message(message)
                except Exception:
                    pass


LOBBY = LobbyState()


class RequestHandler(socketserver.StreamRequestHandler):
    """
    Each client connects and speaks JSON messages terminated by newline.
    We expect an initial {"type":"join","client_id":"name"} from each client.
    """
    def handle(self):
        self.client_id = None
        self.connection.settimeout(None)
        try:
            for raw in self.rfile:
                try:
                    line = raw.decode("utf-8").strip()
                except Exception:
                    continue
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except Exception:
                    continue
                mtype = msg.get("type")
                if mtype == "join":
                    cid = msg.get("client_id")
                    if not cid:
                        self.send_message({"type": "error", "message": "no client_id"})
                        continue
                    # attempt to add
                    ok = LOBBY.add(cid, self)
                    if not ok:
                        self.send_message({"type": "error", "message": "lobby_full"})
                        break
                    self.client_id = cid
                    self.send_message({"type": "joined", "client_id": cid})
                    LOBBY.broadcast({"type": "lobby_update", "clients": LOBBY.list_clients()})
                elif mtype == "start_level":
                    # leader requested a level start; server will spawn mobs scaled to player count
                    level_no = int(msg.get("level", 1))
                    players = len(LOBBY.list_clients())
                    level = Level(level_no)
                    mobs = level.spawn_mobs(player_count=players)
                    # serialize mobs minimally
                    mobs_ser = [{"name": m.name, "hp": m.hp, "attack": m.attack, "defense": m.defense, "crystal_drop": getattr(m, "crystal_drop", 0)} for m in mobs]
                    LOBBY.broadcast({"type": "level_started", "level": level_no, "player_count": players, "mobs": mobs_ser})
                elif mtype == "leave":
                    break
                else:
                    # unknown message - echo to others
                    pass
        finally:
            if getattr(self, "client_id", None):
                LOBBY.remove(self.client_id)
                LOBBY.broadcast({"type": "lobby_update", "clients": LOBBY.list_clients()})

    def send_message(self, msg: Dict):
        raw = json.dumps(msg, separators=(",", ":")) + "\n"
        try:
            self.wfile.write(raw.encode("utf-8"))
            self.wfile.flush()
        except Exception:
            pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def start_server(host: str = "0.0.0.0", port: int = 6000):
    server = ThreadedTCPServer((host, port), RequestHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"Multiplayer server started on {host}:{port} (max players {MAX_PLAYERS})")
    return server