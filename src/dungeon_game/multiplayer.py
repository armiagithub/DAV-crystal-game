from typing import Dict, Any, List
from .game import Game
from .entities import Player
from .level import Level


class GameHost:
    """
    A small helper that could be used server-side to coordinate a multiplayer game.
    It is intentionally minimal — it spawns levels by player count and can be extended
    to maintain full round-by-round state and authoritative damage resolution.
    """
    def __init__(self, players: Dict[str, Player], max_levels: int = 50):
        self.players = players
        self.current_level = 1
        self.max_levels = max_levels
        self.history: List[Dict] = []

    def start_level(self) -> Dict:
        player_count = max(1, len(self.players))
        lvl = Level(self.current_level)
        mobs = lvl.spawn_mobs(player_count=player_count)
        # Minimal simulation: each player sequentially attacks mobs until they are dead.
        # For a real multiplayer experience you'd want an authoritative tick-based simulation.
        kills = 0
        crystals = 0
        for mob in mobs:
            for pname, player in self.players.items():
                if not player.is_alive():
                    continue
                while mob.is_alive() and player.is_alive():
                    dmg = player.attack_target(mob)
                    if mob.is_alive():
                        player.take_damage(mob.attack)
                    else:
                        kills += 1
                        crystals += getattr(mob, "crystal_drop", 0)
                        break
        # Distribute crystals equally (simple)
        if self.players:
            per_player = crystals // len(self.players)
            for player in self.players.values():
                player.gain_crystals(per_player)
        result = {
            "level": self.current_level,
            "player_count": player_count,
            "kills": kills,
            "crystals_gained_total": crystals,
        }
        self.history.append(result)
        self.current_level += 1
        return result