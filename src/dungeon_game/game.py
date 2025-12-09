from .entities import Player, Mob, create_warrior, create_archer, create_sorcerer
from .level import Level
from .shop import Shop
from typing import List
import random


class Game:
    def __init__(self, player: Player, max_levels: int = 50, player_count: int = 1):
        self.player = player
        self.current_level = 1
        self.max_levels = max_levels
        self.history = []
        self.player_count = max(1, player_count)

    def run_level(self, level_number: int, player_count: int = 1) -> dict:
        lvl = Level(level_number)
        mobs: List[Mob] = lvl.spawn_mobs(player_count=player_count)
        kills = 0
        crystals_gained = 0
        xp_gained = 0

        for mob in mobs:
            # Simple combat loop: player attacks until mob dead, mob retaliates once per loop if alive
            while mob.is_alive() and self.player.is_alive():
                dmg = self.player.attack_target(mob)
                # mob retaliates if still alive
                if mob.is_alive():
                    self.player.take_damage(mob.attack)
                else:
                    kills += 1
                    crystals_gained += getattr(mob, "crystal_drop", 0)
                    xp_gained += getattr(mob, "xp_reward", 0)

            if not self.player.is_alive():
                break

        self.player.gain_crystals(crystals_gained)
        result = {
            "level": level_number,
            "player_alive": self.player.is_alive(),
            "kills": kills,
            "crystals_gained": crystals_gained,
            "xp_gained": xp_gained,
            "player_hp": self.player.hp,
            "player_crystals": self.player.crystals,
        }
        self.history.append(result)
        return result

    def open_shop_if_needed(self, level_number: int):
        if level_number % 5 == 0:
            shop = Shop(level_number)
            return shop
        return None

    @staticmethod
    def create_player_by_class(choice: str, name: str = "") -> Player:
        name = name or choice
        choice = choice.lower()
        if choice == "warrior":
            return create_warrior(name)
        if choice == "archer":
            return create_archer(name)
        if choice == "sorcerer":
            return create_sorcerer(name)
        # default
        return create_warrior(name)