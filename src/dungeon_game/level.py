from typing import List
from .entities import Mob
import random


class Level:
    def __init__(self, number: int, difficulty: float = 1.0):
        self.number = number
        self.difficulty = difficulty

    def spawn_mobs(self, player_count: int = 1) -> List[Mob]:
        """
        Spawn a small group of mobs scaled to the level and number of players.

        player_count increases mob HP and attack by a small multiplier so multiplayer
        is more challenging. Example multiplier: 1 + 0.15*(players-1)
        """
        base_count = 3
        count = base_count + (self.number // 3)  # increase mob count slowly
        # small increase in count for more players to keep fights meaningful
        count += max(0, player_count - 1)

        mobs = []
        # scaling multiplier by player count
        player_multiplier = 1.0 + 0.15 * max(0, player_count - 1)

        for i in range(count):
            # Scale mob stats by level and players
            hp = int(20 * (1 + self.number * 0.08) * self.difficulty * player_multiplier)
            attack = int(5 * (1 + self.number * 0.05) * self.difficulty * player_multiplier)
            defense = int(1 + self.number * 0.02 + (player_count - 1))
            xp = int(5 * (1 + self.number * 0.1))
            crystals = max(1, int(1 * (1 + self.number * 0.06) * player_multiplier))
            mobs.append(Mob(name=f"Mob_L{self.number}_{i+1}", hp=hp, attack=attack, defense=defense, xp_reward=xp, crystal_drop=crystals))
        random.shuffle(mobs)
        return mobs