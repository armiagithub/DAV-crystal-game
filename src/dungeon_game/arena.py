# arena.py - arena gameplay, waves, death handling, inventory equip by number keys
import math
import random
import time
from typing import List, Tuple, Optional
import pygame
from pathlib import Path

from .level import Level
from .shop import Shop
from .entities import create_warrior, create_archer, create_sorcerer, create_rogue, create_paladin, create_necromancer, Player, Mob, Item

Vec2 = Tuple[float, float]

ASSET_DIR = Path(__file__).resolve().parent / "assets" / "images"

def load_image(name: str, size: Tuple[int,int]=None) -> Optional[pygame.Surface]:
    """
    Load an image from the package assets/images folder. Returns a pygame.Surface or None.
    This is a small helper so other modules (gui.py) can import a single loader.
    """
    p = ASSET_DIR / name
    if not p.exists():
        return None
    try:
        img = pygame.image.load(str(p))
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img.convert_alpha()
    except Exception:
        return None

def vec_len(v: Vec2) -> float:
    return math.hypot(v[0], v[1])


def vec_norm(v: Vec2) -> Vec2:
    l = vec_len(v)
    if l == 0:
        return (0.0, 0.0)
    return (v[0] / l, v[1] / l)


class Projectile:
    def __init__(self, x: float, y: float, vx: float, vy: float, damage: int, life: float = 2.0, image: Optional[pygame.Surface] = None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.life = life  # seconds
        self.spawn = time.time()
        # if an image is supplied, keep it and set radius from image size; otherwise use default small radius
        self.image = image
        if self.image:
            w, h = self.image.get_size()
            self.radius = max(4, int(max(w, h) / 2))
        else:
            self.radius = 4

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def is_expired(self) -> bool:
        return (time.time() - self.spawn) > self.life


class ArenaMob:
    def __init__(self, mob: Mob, x: float, y: float, image: Optional[pygame.Surface] = None):
        self.mob = mob
        self.x = x
        self.y = y
        # if an image is supplied, use its size to determine radius and keep the image for rendering
        self.image = image
        if self.image:
            w, h = self.image.get_size()
            self.radius = max(8, int(max(w, h) / 2))
        else:
            self.radius = max(8, int(mob.hp ** 0.4))  # visual size
        self.speed = max(20.0, 40.0 - mob.defense * 2)  # mobs slower if high defense
        self.color = (200, 80, 80)
        # choose look by kind (used when image not provided)
        if getattr(mob, "kind", "") == "slime":
            self.color = (80, 200, 120)
        elif getattr(mob, "kind", "") == "skeleton":
            self.color = (220, 220, 200)
        elif getattr(mob, "kind", "") == "fire":
            self.color = (240, 120, 40)
        elif getattr(mob, "kind", "") == "wolf":
            self.color = (140, 80, 40)
        elif getattr(mob, "kind", "") == "poison":
            self.color = (120, 200, 140)

    def is_alive(self) -> bool:
        return self.mob.is_alive()

    def take_damage(self, amount: int):
        return self.mob.take_damage(amount)

    def update(self, dt: float, target_x: float, target_y: float):
        if not self.is_alive():
            return
        dx = target_x - self.x
        dy = target_y - self.y
        nd = vec_norm((dx, dy))
        self.x += nd[0] * self.speed * dt
        self.y += nd[1] * self.speed * dt


class ArenaPlayer:
    def __init__(self, player: Player, x: float, y: float):
        # keep reference to the 'Player' dataclass for crystals / inventory bookkeeping
        self.player = player
        self.x = x
        self.y = y
        self.radius = 12
        self.speed = 180.0
        self.color = (80, 160, 220)
        # melee/ranged params
        self.melee_cooldown_until = 0.0
        self.melee_cooldown = 0.6
        self.melee_range = 28
        self.ranged_cooldown = 0.4
        self.last_ranged = 0.0
        # auto-fire tracking (used by artifact/amulet)
        self.last_auto_fire = 0.0

    def is_alive(self) -> bool:
        return self.player.is_alive()

    def move(self, dx: float, dy: float, dt: float, bounds: Tuple[int, int]):
        if dx == 0 and dy == 0:
            return
        nd = vec_norm((dx, dy))
        self.x = max(self.radius, min(bounds[0] - self.radius, self.x + nd[0] * self.speed * dt))
        self.y = max(self.radius, min(bounds[1] - self.radius, self.y + nd[1] * self.speed * dt))

    def melee_attack(self, mobs: List[ArenaMob]) -> List[Tuple[ArenaMob, int]]:
        now = time.time()
        if now < self.melee_cooldown_until:
            return []
        self.melee_cooldown_until = now + self.melee_cooldown
        hits = []
        for m in mobs:
            if not m.is_alive():
                continue
            dx = m.x - self.x
            dy = m.y - self.y
            if math.hypot(dx, dy) <= self.melee_range + m.radius:
                # use player's attack stat (recomputed in Player)
                damage = max(0, self.player.attack - m.mob.defense)
                if damage <= 0:
                    damage = 1
                m.take_damage(damage)
                hits.append((m, damage))
        return hits

    def ranged_attack(self, target_pos: Tuple[int, int], image: Optional[pygame.Surface] = None) -> Optional[Projectile]:
        """
        Fire a projectile toward target_pos. If image is provided it will be attached to the Projectile.
        """
        now = time.time()
        if now - self.last_ranged < self.ranged_cooldown:
            return None
        self.last_ranged = now
        dx = target_pos[0] - self.x
        dy = target_pos[1] - self.y
        nd = vec_norm((dx, dy))
        speed = 400.0
        vx = nd[0] * speed
        vy = nd[1] * speed
        dmg = max(1, self.player.attack // 2)
        return Projectile(self.x + nd[0] * (self.radius + 4), self.y + nd[1] * (self.radius + 4), vx, vy, dmg, life=2.0, image=image)

    def take_damage(self, amount: int):
        """
        Accept a damage value already computed by the scene (scene subtracts defense before calling).
        Subtract it directly from the player's HP to avoid double-defense issues.
        """
        applied = max(0, int(amount))
        self.player.hp = max(0, self.player.hp - applied)
        return applied

    def equip_item(self, item: Item) -> bool:
        """
        Add item to inventory or equip directly into the appropriate slot.
        Returns True if placed/equipped else False.
        """
        # prefer to add to first inventory slot if empty
        placed = self.player.add_to_inventory(item)
        return placed