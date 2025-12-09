from dataclasses import dataclass, field
import random
from typing import Dict


@dataclass
class Entity:
    name: str
    hp: int
    attack: int
    defense: int

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        damage = max(0, amount - self.defense)
        self.hp = max(0, self.hp - damage)
        return damage


@dataclass
class Mob(Entity):
    xp_reward: int = 0
    crystal_drop: int = 0


@dataclass
class Item:
    name: str
    attack_bonus: int = 0
    defense_bonus: int = 0
    cost: int = 0
    tier: int = 1


@dataclass
class Player(Entity):
    level: int = 1
    crystals: int = 0
    xp: int = 0
    inventory: Dict[str, Item] = field(default_factory=dict)

    def equip(self, item: Item):
        self.inventory[item.name] = item
        self.attack += item.attack_bonus
        self.defense += item.defense_bonus

    def gain_crystals(self, amount: int):
        self.crystals += amount

    def attack_target(self, target: Entity) -> int:
        base = self.attack
        damage = target.take_damage(base)
        return damage

    def heal(self, amount: int):
        self.hp += amount


# Class-specific factories for easy creation with different base stats
def create_warrior(name: str = "Warrior") -> Player:
    return Player(name=name, hp=120, attack=14, defense=6)


def create_archer(name: str = "Archer") -> Player:
    return Player(name=name, hp=90, attack=16, defense=3)


def create_sorcerer(name: str = "Sorcerer") -> Player:
    return Player(name=name, hp=75, attack=18, defense=2)