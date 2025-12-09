import pygame
import threading
import time
from .game import Game
from .game import Game as G
from .entities import create_warrior, create_archer, create_sorcerer
from .persistence import LocalProfile, OnlineAuthClient if False else None  # noqa: F401
from .network import GameClient

# Simple GUI constants
WIDTH, HEIGHT = 800, 600
FPS = 30


class DungeonGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Dungeon - Prototype GUI")
        self.clock = pygame.time.Clock()
        self.running = True

        # UI state
        self.username = "Player"
        self.player_class = "warrior"
        self.mode = "local"  # local | host | connect
        self.server_host = "localhost"
        self.server_port = 6000

        # network client (for connect mode)
        self.net_client = None
        self.messages = []

    def draw_text(self, surf, text, pos, size=24, color=(255, 255, 255)):
        font = pygame.font.SysFont("arial", size)
        surf.blit(font.render(text, True, color), pos)

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.running = False
                    # quick toggles for demo
                    elif ev.key == pygame.K_1:
                        self.player_class = "warrior"
                    elif ev.key == pygame.K_2:
                        self.player_class = "archer"
                    elif ev.key == pygame.K_3:
                        self.player_class = "sorcerer"
                    elif ev.key == pygame.K_h:
                        self.mode = "host"
                    elif ev.key == pygame.K_c:
                        self.mode = "connect"
                    elif ev.key == pygame.K_l:
                        self.mode = "local"
                    elif ev.key == pygame.K_SPACE:
                        # start a local single-player demo run (blocking small thread)
                        t = threading.Thread(target=self._run_local_demo, daemon=True)
                        t.start()

            self.screen.fill((30, 30, 40))
            self.draw_text(self.screen, f"Mode: {self.mode}  (press L-local, H-host, C-connect)", (20, 20))
            self.draw_text(self.screen, f"Class: {self.player_class}  (1:warrior 2:archer 3:sorcerer)", (20, 60))
            self.draw_text(self.screen, f"Username: {self.username}", (20, 100))
            self.draw_text(self.screen, "Press SPACE to start a local demo run (single-player)", (20, 140), size=18)
            self.draw_text(self.screen, "Press H to start a local host server (in-process) or C to connect to server", (20, 170), size=18)
            # messages area
            y = 220
            for m in self.messages[-6:]:
                self.draw_text(self.screen, str(m), (20, y), size=18, color=(200, 200, 120))
                y += 24

            pygame.display.flip()
        pygame.quit()

    def _run_local_demo(self):
        # create player and run a short demo
        player = Game.create_player_by_class(self.player_class, self.username)
        game = Game(player, max_levels=10)
        for lvl in range(1, game.max_levels + 1):
            if not player.is_alive():
                self.messages.append("You died.")
                break
            res = game.run_level(lvl, player_count=1)
            self.messages.append(f"Level {lvl}: kills={res['kills']} crystals={res['crystals_gained']}")
            # small delay so messages are readable
            time.sleep(0.6)
        self.messages.append("Local demo finished.")


def launch_gui():
    gui = DungeonGUI()
    gui.run()