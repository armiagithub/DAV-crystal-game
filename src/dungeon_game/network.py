import socket
import json
import threading
from typing import Callable, Optional


# Simple newline-delimited JSON protocol
class GameClient:
    def __init__(self, host: str = "localhost", port: int = 6000, on_message: Optional[Callable] = None):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self._recv_thread: Optional[threading.Thread] = None
        self._running = False
        self.on_message = on_message

    def connect(self, timeout: float = 5.0) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((self.host, self.port))
        self.sock.settimeout(None)
        self._running = True
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def close(self):
        self._running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            self.sock.close()
        self.sock = None

    def send(self, payload: dict):
        if not self.sock:
            raise RuntimeError("Not connected")
        data = json.dumps(payload, separators=(",", ":")) + "\n"
        self.sock.sendall(data.encode("utf-8"))

    def _recv_loop(self):
        buff = ""
        try:
            while self._running and self.sock:
                data = self.sock.recv(4096).decode("utf-8")
                if not data:
                    break
                buff += data
                while "\n" in buff:
                    line, buff = buff.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line)
                    except Exception:
                        continue
                    if self.on_message:
                        try:
                            self.on_message(msg)
                        except Exception:
                            pass
        except Exception:
            pass
        finally:
            self.close()