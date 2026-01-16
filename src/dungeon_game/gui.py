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

# Simple animation helper
class Animation:
    def __init__(self, frames: List[pygame.Surface], frame_duration: float = 0.08, loop: bool = False):
        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop
        self.start = time.time()
        self.finished = False

    def current_frame(self) -> Optional[pygame.Surface]:
        if not self.frames:
            return None
        elapsed = time.time() - self.start
        idx = int(elapsed / self.frame_duration)
        if idx >= len(self.frames):
            if self.loop:
                idx = idx % len(self.frames)
            else:
                self.finished = True
                idx = len(self.frames) - 1
        return self.frames[idx]

    def is_done(self) -> bool:
        return self.finished


def try_load(name, size=None):
    p = ASSET_DIR / name
    if p.exists():
        try:
            img = pygame.image.load(str(p))
            if size:
                img = pygame.transform.smoothscale(img, size)
            return img.convert_alpha()
        except Exception:
            return None
    return None

# fallback colors for classes so they are visibly different without art
CLASS_FALLBACK_COLOR = {
    "warrior": (80, 160, 220),
    "archer": (120, 200, 120),
    "sorcerer": (200, 120, 220),
    "rogue": (200, 180, 80),
    "paladin": (200, 200, 160),
    "necromancer": (120, 160, 200),
}

# weapon->animation file patterns expected:
# weapon_{key}_anim_0.png, weapon_{key}_anim_1.png, weapon_{key}_anim_2.png, ...
def load_weapon_animation(key: str, frames: int = 3, size: Tuple[int,int]=None) -> List[pygame.Surface]:
    frames_list = []
    for i in range(frames):
        name = f"weapon_{key}_anim_{i}.png"
        img = try_load(name, size=size)
        if img is None:
            break
        frames_list.append(img)
    return frames_list

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

        # load weapon animations keyed by simple names we expect items to use:
        self.weapon_anims: Dict[str, List[pygame.Surface]] = {
            "sword": load_weapon_animation("sword", frames=3, size=(64,64)),
            "bow": load_weapon_animation("bow", frames=3, size=(64,64)),
            "staff": load_weapon_animation("staff", frames=3, size=(64,64)),
            "dagger": load_weapon_animation("dagger", frames=3, size=(64,64)),
            "hammer": load_weapon_animation("hammer", frames=3, size=(64,64)),
        }
        # active transient animations (melee swings, special effects) as list of (Animation, x, y)
        self.active_animations: List[Tuple[Animation, int, int]] = []

        # projectile image
        self.img_proj = try_load("proj_arrow.png", size=(24,8))
        # mob images map
        self.img_mobs = {
            "slime": try_load("mob_slime.png", size=(48,48)),
            "skeleton": try_load("mob_skeleton.png", size=(48,48)),
            "fire": try_load("mob_fire.png", size=(48,48)),
            "wolf": try_load("mob_wolf.png", size=(48,48)),
            "poison": try_load("mob_poison.png", size=(48,48)),
        }

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
        """
        Spawn a wave of mobs for the current level.
        - append=False (default) clears previous mobs/projectiles and starts fresh (used for first wave)
        - append=True will add the new wave's mobs to self.mobs without removing existing living mobs
        After spawning, schedules the next wave after delay_next seconds (if there are more waves).
        """
        if not append:
            # fresh wave: clear projectiles and mobs
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
        # schedule next wave if appropriate
        if self.current_wave < self.waves_total:
            d = delay_next if delay_next is not None else self.default_inter_wave_delay
            self.next_wave_time = time.time() + d
        else:
            self.next_wave_time = None

    def start_level(self):
        self.current_wave = 0
        self.show_shop_overlay = True
        self.current_shop = Shop(self.level_no, self.player_class)
        self.awaiting_replace = False
        self.pending_purchase_item = None
        self.coins = 0
        self.next_wave_time = None

    def _spawn_weapon_anim_for_item(self, item: Item, x: int, y: int):
        # determine anim key from item.name or type; simple heuristics:
        key = None
        name_lower = item.name.lower()
        if "sword" in name_lower or "axe" in name_lower or item.type == "melee":
            key = "sword"
        elif "bow" in name_lower or item.type == "ranged":
            key = "bow"
        elif "staff" in name_lower or item.type == "magic":
            key = "staff"
        elif "dagger" in name_lower:
            key = "dagger"
        elif "hammer" in name_lower:
            key = "hammer"
        if key and self.weapon_anims.get(key):
            frames = self.weapon_anims[key]
            anim = Animation(frames, frame_duration=0.08, loop=False)
            self.active_animations.append((anim, x, y))

    def update(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        # if a next wave was scheduled, check and spawn (append) when time reached
        if self.next_wave_time and now >= self.next_wave_time and self.current_wave < self.waves_total:
            # append next wave while previous may still be alive
            self.spawn_wave(append=True)
            # spawn_wave will set next_wave_time for subsequent waves

        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        self.arena_player.move(dx, dy, dt, (WIDTH, HEIGHT))

        # update animations list (remove finished)
        for anim, ax, ay in list(self.active_animations):
            if anim.is_done():
                try:
                    self.active_animations.remove((anim, ax, ay))
                except ValueError:
                    pass

        for p in list(self.projectiles):
            p.update(dt)
            if p.is_expired():
                try:
                    self.projectiles.remove(p)
                except ValueError:
                    pass
                continue
            for m in self.mobs:
                if not m.is_alive():
                    continue
                if (p.x - m.x) ** 2 + (p.y - m.y) ** 2 <= (p.radius + m.radius) ** 2:
                    m.take_damage(p.damage)
                    if p in self.projectiles:
                        try:
                            self.projectiles.remove(p)
                        except Exception:
                            pass
                    break

        # mob updates and collision with player
        for m in self.mobs:
            if m.is_alive():
                m.update(dt, self.arena_player.x, self.arena_player.y)
                if (m.x - self.arena_player.x) ** 2 + (m.y - self.arena_player.y) ** 2 <= (m.radius + self.arena_player.radius) ** 2:
                    dmg = max(1, m.mob.attack - self.arena_player.player.defense)
                    # arena_player.take_damage expects already-computed damage (no double-defense)
                    self.arena_player.take_damage(dmg)

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
            # accumulate per-level coins (used for shop this level)
            self.coins += gained
            self.shop_message = f"+{gained} coins (session {self.coins})"

        # Auto-fire artifact logic: if player has an equipped artifact and a ranged weapon, periodically fire.
        if self.player.equipped_artifact and self.player.equipped_ranged:
            art = self.player.equipped_artifact
            tier = getattr(art, "tier", 1)
            # base cooldown decreased with higher tiers (tweak as desired)
            cooldown = max(0.6 - (tier - 1) * 0.12, 0.12)
            nowt = time.time()
            if nowt - self.arena_player.last_auto_fire >= cooldown:
                # choose a target if tier >=2 (auto-aim nearest), else shoot forward
                tx = self.arena_player.x + 120
                ty = self.arena_player.y
                if tier >= 2:
                    live = [mm for mm in self.mobs if mm.is_alive()]
                    if live:
                        target_m = min(live, key=lambda mm: (mm.x - self.arena_player.x) ** 2 + (mm.y - self.arena_player.y) ** 2)
                        tx, ty = target_m.x, target_m.y
                proj = self.arena_player.ranged_attack((tx, ty), image=self.img_proj)
                if proj:
                    self.projectiles.append(proj)
                    if self.player.equipped_ranged:
                        self._spawn_weapon_anim_for_item(self.player.equipped_ranged, int(self.arena_player.x + (tx - self.arena_player.x) * 0.2), int(self.arena_player.y + (ty - self.arena_player.y) * 0.2))
                    self.arena_player.last_auto_fire = nowt

        # When all waves spawned and no mobs remain -> level cleared
        if self.current_wave > 0 and self.current_wave >= self.waves_total and all(not m.is_alive() for m in self.mobs):
            # award permanent crystal for clearing the dungeon
            self.player.gain_crystals(1)
            self.shop_message = f"Cleared level {self.level_no}! +1 crystal (total {self.player.crystals})."
            # reset per-level coins and advance level
            self.coins = 0
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
        self.player.hp = self.player.max_hp
        self.level_no = 1
        # YOU LOSE your coins on death:
        self.coins = 0
        # restart level/shop state
        self.start_level()
        self.save_state()

    def draw(self):
        self.screen.fill((28, 28, 36))
        # draw player (image or colored circle)
        if self.img_player:
            rect = self.img_player.get_rect(center=(int(self.arena_player.x), int(self.arena_player.y)))
            self.screen.blit(self.img_player, rect)
        else:
            color = CLASS_FALLBACK_COLOR.get(self.player_class, (160,160,160))
            pygame.draw.circle(self.screen, color, (int(self.arena_player.x), int(self.arena_player.y)), self.arena_player.radius)

        # draw mobs (images or circles)
        for m in self.mobs:
            if m.image:
                rect = m.image.get_rect(center=(int(m.x), int(m.y)))
                self.screen.blit(m.image, rect)
            else:
                if m.is_alive():
                    pygame.draw.circle(self.screen, m.color, (int(m.x), int(m.y)), m.radius)
                else:
                    pygame.draw.circle(self.screen, (80, 80, 80), (int(m.x), int(m.y)), max(6, m.radius//2))

        # draw projectiles
        for p in self.projectiles:
            if p.image:
                rect = p.image.get_rect(center=(int(p.x), int(p.y)))
                self.screen.blit(p.image, rect)
            else:
                pygame.draw.circle(self.screen, (220, 220, 120), (int(p.x), int(p.y)), p.radius)

        # draw active animations (melee swings etc)
        for anim, ax, ay in list(self.active_animations):
            frame = anim.current_frame()
            if frame:
                rect = frame.get_rect(center=(ax, ay))
                self.screen.blit(frame, rect)

        # HUD
        self._draw_text(f"Level: {self.level_no}", 10, 8)
        self._draw_text(f"Wave: {max(0, self.current_wave)}/{self.waves_total}", 90, 8)
        self._draw_text(f"HP: {self.player.hp}/{self.player.max_hp}", 180, 8)
        # show both coins (session) and crystals (permanent)
        self._draw_text(f"Coins: {self.coins}  Crystals: {self.player.crystals}", 340, 8)

        eqs = []
        if self.player.equipped_melee:
            eqs.append(f"M:{self.player.equipped_melee.name}")
        if self.player.equipped_ranged:
            eqs.append(f"R:{self.player.equipped_ranged.name}")
        if self.player.equipped_magic:
            eqs.append(f"S:{self.player.equipped_magic.name}")
        if self.player.equipped_artifact:
            eqs.append(f"A:{self.player.equipped_artifact.name}")
        self._draw_text("Equipped: " + (", ".join(eqs) if eqs else "None"), 520, 8)

        # inventory display
        inv_x = 10
        inv_y = HEIGHT - 40
        slot_w = 72
        size = self.player.effective_inventory_size()
        for i in range(size):
            rect = pygame.Rect(inv_x + i * (slot_w + 4), inv_y, slot_w, 32)
            pygame.draw.rect(self.screen, (40, 40, 60), rect)
            pygame.draw.rect(self.screen, (70, 70, 90), rect, 2)
            it = self.player.inventory[i] if i < len(self.player.inventory) else None
            label = str((i+1)%10)
            if it:
                txt = f"{label}:{it.name[:10]}"
            else:
                txt = f"{label}: empty"
            self._draw_text(txt, rect.x + 6, rect.y + 6, color=(200, 200, 200))

        if self.shop_message:
            self._draw_text(self.shop_message, 10, HEIGHT - 68, color=(200, 200, 120))

        if self.show_shop_overlay and self.current_shop:
            self._draw_shop_overlay()

    def _draw_text(self, txt: str, x: int, y: int, color=(220, 220, 220)):
        surf = self.font.render(txt, True, color)
        self.screen.blit(surf, (x, y))

    def _draw_shop_overlay(self):
        s = pygame.Surface((WIDTH - 120, HEIGHT - 120), pygame.SRCALPHA)
        s.fill((10, 10, 10, 220))
        self.screen.blit(s, (60, 60))
        title = f"Shop - Level {self.level_no} - Coins: {self.coins}  Crystals: {self.player.crystals}"
        t = self.font.render(title, True, (255, 255, 200))
        self.screen.blit(t, (80, 80))
        items = self.current_shop.list_items()
        y = 120
        for idx, it in enumerate(items, start=1):
            line = f"{idx}. {it.name} (ATK+{it.attack_bonus} DEF+{it.defense_bonus}) - Cost: {it.cost}"
            color = (200, 200, 200) if self.coins >= it.cost else (120, 120, 120)
            self.screen.blit(self.font.render(line, True, color), (80, y))
            y += 28
        help_text = "Press number to buy (uses Coins), ESC to close shop."
        if self.awaiting_replace:
            help_text = "Inventory full — press slot number (1..9,0) to replace that item with the purchase, or ESC to cancel."
        self.screen.blit(self.font.render(help_text, True, (200, 200, 200)), (80, y + 8))

    def _attempt_buy(self, item: Item, replace_index: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Try to buy 'item' using self.coins. Returns (success, info).
        - If purchased and placed in inventory: (True, None)
        - If inventory full and replace_index is None: (False, "inventory_full")
        - If replace_index provided: perform replace and return (True, replaced_name)
        - If not enough coins: (False, "not_enough")
        """
        if self.coins < item.cost:
            return False, "not_enough"
        # deduct coins now
        self.coins -= item.cost
        placed = self.player.add_to_inventory(item)
        if placed:
            return True, None
        # inventory full
        if replace_index is None:
            # refund coins
            self.coins += item.cost
            return False, "inventory_full"
        try:
            replaced = self.player.swap_inventory_slot(replace_index, item)
        except IndexError:
            self.coins += item.cost
            return False, "invalid_slot"
        replaced_name = replaced.name if replaced else None
        return True, replaced_name

    def handle_event(self, ev: pygame.event.Event):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and not self.show_shop_overlay:
            mx, my = ev.pos
            proj = self.arena_player.ranged_attack((mx, my), image=self.img_proj)
            if proj:
                # attach projectile image if available
                self.projectiles.append(proj)
                # spawn a small ranged-shot anim at player location based on equipped ranged item
                if self.player.equipped_ranged:
                    self._spawn_weapon_anim_for_item(self.player.equipped_ranged, int(self.arena_player.x + (mx - self.arena_player.x)*0.2), int(self.arena_player.y + (my - self.arena_player.y)*0.2))
        elif ev.type == pygame.KEYDOWN:
            # number keys equip inventory slot if not in shop
            if ev.unicode.isdigit() and not self.show_shop_overlay:
                digit = ev.unicode
                slot_idx = (int(digit) - 1) if digit != "0" else 9
                ok = self.player.equip_from_inventory(slot_idx)
                if ok:
                    self.shop_message = f"Equipped from slot {slot_idx+1}"
                else:
                    self.shop_message = "Cannot equip that slot (empty or no space to swap)."
            elif ev.key == pygame.K_SPACE and not self.show_shop_overlay:
                # melee attack: perform damage and spawn a melee anim depending on equipped melee item
                hits = self.arena_player.melee_attack(self.mobs)
                if hits:
                    self.shop_message = f"Hit {len(hits)} mob(s)"
                if self.player.equipped_melee:
                    # spawn melee animation in front of player
                    mx, my = pygame.mouse.get_pos()
                    anim_x = int(self.arena_player.x + (mx - self.arena_player.x) * 0.4)
                    anim_y = int(self.arena_player.y + (my - self.arena_player.y) * 0.4)
                    self._spawn_weapon_anim_for_item(self.player.equipped_melee, anim_x, anim_y)
            elif ev.key == pygame.K_ESCAPE:
                # If shop overlay is visible, ESC closes or cancels pending replacement
                if self.show_shop_overlay:
                    if self.awaiting_replace and self.pending_purchase_item:
                        # cancel pending replace, refund if necessary
                        self.awaiting_replace = False
                        self.pending_purchase_item = None
                        self.shop_message = "Purchase canceled."
                    else:
                        # close overlay and, if no waves started, spawn first wave
                        self.show_shop_overlay = False
                        if self.current_wave == 0:
                            self.spawn_wave()
                else:
                    # If no overlay, ESC now just pauses (open a simple pause overlay) -- do NOT reopen shop
                    self.shop_message = "Paused. Press ESC again to open shop."
                    # toggling to shop is not automatic anymore
            elif self.show_shop_overlay and ev.unicode.isdigit():
                # buying logic (using coins)
                if self.awaiting_replace and self.pending_purchase_item:
                    digit = ev.unicode
                    slot_idx = (int(digit) - 1) if digit != "0" else 9
                    success, info = self._attempt_buy(self.pending_purchase_item, replace_index=slot_idx)
                    if success:
                        self.shop_message = f"Bought {self.pending_purchase_item.name} replacing slot {slot_idx+1}"
                    else:
                        self.shop_message = f"Replace failed: {info}"
                    self.awaiting_replace = False
                    self.pending_purchase_item = None
                else:
                    digit = ev.unicode
                    choice = int(digit)
                    items = self.current_shop.list_items()
                    idx = choice - 1
                    if 0 <= idx < len(items):
                        item = items[idx]
                        success, info = self._attempt_buy(item)
                        if success:
                            self.shop_message = f"Bought {item.name}"
                        else:
                            if info == "inventory_full":
                                # set awaiting_replace, keep the pending item in memory (no refund)
                                self.awaiting_replace = True
                                self.pending_purchase_item = item
                                self.shop_message = "Inventory full — press slot number to replace, or ESC to cancel."
                            elif info == "not_enough":
                                self.shop_message = "Not enough coins."
                            else:
                                self.shop_message = f"Buy failed: {info}"
            # ensure wave spawns if shop closed and no wave started
            if not self.show_shop_overlay and self.current_wave == 0:
                self.spawn_wave()

# simplified launcher that uses ArenaScene
if 'launch_gui' not in globals():
    def launch_gui():
        pygame.init()
        # Use RESIZABLE so maximize button is available; keep SCALED for DPI scaling if supported
        flags = pygame.RESIZABLE | getattr(pygame, "SCALED", 0)
        screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.display.set_caption("Dungeon - Arena Demo")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("arial", 20)
        choice = "warrior"
        username = "Player"
        prompt = "Choose class: 1:Warrior 2:Archer 3:Sorcerer 4:Rogue 5:Paladin 6:Necromancer  Press Enter to start"
        running = True
        while running:
            screen.fill((24, 24, 32))
            screen.blit(font.render(prompt, True, (220, 220, 220)), (20, 20))
            screen.blit(font.render(f"Selected: {choice}", True, (200, 200, 100)), (20, 60))
            screen.blit(font.render("WASD to move, Mouse Left to shoot, Space to melee. Shop before first wave and after each level.", True, (180, 180, 180)), (20, 100))
            pygame.display.flip()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_1:
                        choice = "warrior"
                    elif ev.key == pygame.K_2:
                        choice = "archer"
                    elif ev.key == pygame.K_3:
                        choice = "sorcerer"
                    elif ev.key == pygame.K_4:
                        choice = "rogue"
                    elif ev.key == pygame.K_5:
                        choice = "paladin"
                    elif ev.key == pygame.K_6:
                        choice = "necromancer"
                    elif ev.key == pygame.K_RETURN:
                        scene = ArenaScene(screen, choice, username)
                        # simple scene loop:
                        running_inner = True
                        clock_inner = pygame.time.Clock()
                        while running_inner:
                            dt = clock_inner.tick(FPS) / 1000.0
                            for ev2 in pygame.event.get():
                                if ev2.type == pygame.QUIT:
                                    running_inner = False
                                    running = False
                                else:
                                    scene.handle_event(ev2)
                            if not scene.show_shop_overlay:
                                scene.update()
                            scene.draw()
                            pygame.display.flip()
                        scene.save_state()
                    elif ev.key == pygame.K_ESCAPE:
                        running = False
            clock.tick(30)
        pygame.quit()
