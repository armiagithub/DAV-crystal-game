# (file header omitted here; this block replaces the same file in your repo)
# Updated GUI: fixed ESC behavior, per-class sprite fallback, weapon animations
import pygame
import threading
import time
import sys
import random
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from .game import Game
from .entities import create_warrior, create_archer, create_sorcerer, create_rogue, create_paladin, create_necromancer, Player, Item
from .arena import ArenaPlayer, ArenaMob, Projectile, load_image, ASSET_DIR
from .level import Level
from .shop import Shop
try:
    from .persistence import LocalProgress
except Exception:
    LocalProgress = None

WIDTH, HEIGHT = 900, 700
FPS = 60

# ... (unchanged helper classes and functions omitted for brevity) ...

class ArenaScene:
    def __init__(self, screen: pygame.Surface, player_class: str, username: str, max_levels: int = 50):
        self.screen = screen
        self.username = username
        self.player_class = player_class
        # load progress if any
        saved = None
        try:
            saved = LocalProgress.load_progress(username) if LocalProgress else None
        except Exception:
            saved = None
        if saved:
            self.player = Game.create_player_by_class(saved.get("class", player_class), username)
            self.player.crystals = saved.get("crystals", self.player.crystals)
            self.player.hp = saved.get("hp", self.player.max_hp)
            self.player.level = saved.get("level", self.player.level)
        else:
            self.player = Game.create_player_by_class(player_class, username)
        self.arena_player = ArenaPlayer(self.player, WIDTH // 2, HEIGHT // 2)
        self.projectiles: List[Projectile] = []
        self.mobs: List[ArenaMob] = []
        self.level_no = saved.get("level", 1) if saved else 1
        self.max_levels = max_levels
        self.waves_total = 5
        self.current_wave = 0
        self.last_time = time.time()
        self.font = pygame.font.SysFont("arial", 18)
        self.show_shop_overlay = True
        self.current_shop: Optional[Shop] = Shop(self.level_no, player_class)
        self.shop_message = ""
        self.awaiting_replace = False
        self.pending_purchase_item: Optional[Item] = None

        # per-level session currency (coins) separate from permanent crystals:
        self.coins = 0

        # scheduling for waves (allows scheduling next wave even while old waves alive)
        self.next_wave_time: Optional[float] = None
        self.default_inter_wave_delay = 4.0  # seconds between waves when scheduled

        # load player sprite for class, fallback to None (we'll draw a colored circle)
        self.img_player = try_load(f"player_{self.player_class}.png", size=(48,48))

        # ... rest unchanged (weapon_anims, images, etc.) ...

    def save_state(self):
        data = {
            "class": self.player_class,
            "crystals": self.player.crystals,
            "hp": self.player.hp,
            "level": self.level_no,
        }
        if LocalProgress:
            try:
                LocalProgress.save_progress(self.username, data)
            except Exception:
                pass

    def spawn_wave(self, append: bool = False, delay_next: Optional[float] = None):
        if not append:
            self.projectiles = []
            self.mobs = []
        self.current_wave += 1
        lvl = Level(self.level_no)
        mob_list = lvl.spawn_mobs(player_count=1)
        for i, m in enumerate(mob_list):
            rand_x = random.randint(40, WIDTH - 40)
            rand_y = random.randint(40, HEIGHT - 40)
            img = self.img_mobs.get(getattr(m, "kind", ""), None)
            self.mobs.append(ArenaMob(m, rand_x, rand_y, image=img))
        if self.current_wave < self.waves_total:
            d = delay_next if delay_next is not None else self.default_inter_wave_delay
            self.next_wave_time = time.time() + d
        else:
            self.next_wave_time = None

    def start_level(self):
        # NOTE: do NOT reset self.coins here — coins persist across levels during the session.
        self.current_wave = 0
        self.show_shop_overlay = True
        self.current_shop = Shop(self.level_no, self.player_class)
        self.awaiting_replace = False
        self.pending_purchase_item = None
        # keep self.coins as-is so coins persist between levels in the running session
        self.next_wave_time = None

    # ... _spawn_weapon_anim_for_item unchanged ...

    def update(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        # handle scheduled next wave even if previous living mobs remain
        if self.next_wave_time and now >= self.next_wave_time and self.current_wave < self.waves_total:
            self.spawn_wave(append=True)

        # ... movement, projectiles, mob updates unchanged ...

        # collect coin drops from dead mobs
        gained = 0
        for m in list(self.mobs):
            if not m.is_alive():
                gained += getattr(m.mob, "crystal_drop", 0)
                try:
                    self.mobs.remove(m)
                except Exception:
                    pass
        if gained:
            # accumulate per-level coins (used for shop this level and persist across levels)
            self.coins += gained
            self.shop_message = f"+{gained} coins (session {self.coins})"

        # ... auto-fire artifact logic unchanged ...

        # When all waves spawned and no mobs remain -> level cleared
        if self.current_wave > 0 and self.current_wave >= self.waves_total and all(not m.is_alive() for m in self.mobs):
            # award permanent crystal for clearing the dungeon
            self.player.gain_crystals(1)
            self.shop_message = f"Cleared level {self.level_no}! +1 crystal (total {self.player.crystals})."
            # DO NOT reset self.coins here — keep coins across levels in the session
            # advance level
            self.level_no = min(self.level_no + 1, self.max_levels)
            self.show_shop_overlay = True
            self.current_shop = Shop(self.level_no, self.player_class)
            self.save_state()
            # reset waves so next time player closes shop and starts, waves start fresh
            self.current_wave = 0
            self.next_wave_time = None

        if self.player.hp <= 0:
            self.handle_death()

    def handle_death(self):
        lost = self.player.crystals // 2
        self.player.crystals = max(0, self.player.crystals - lost)
        self.player.clear_inventory_and_equipment()
        self.shop_message = f"You died! Lost {lost} crystals. Returning to level 1. Inventory cleared."
        # reset player HP and level
        self.player.hp = self.player.max_hp
        self.level_no = 1
        # YOU LOSE your coins on death:
        self.coins = 0
        # restart level/shop state
        self.start_level()
        self.save_state()

    # ... draw(), _draw_text(), _draw_shop_overlay(), _attempt_buy(), handle_event(), launch_gui() unchanged ...