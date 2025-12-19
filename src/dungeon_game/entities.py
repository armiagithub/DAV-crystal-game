# src/dungeon_game/entities.py
from dataclasses import dataclass, field
import random
from typing import Dict, Optional, List


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
    kind: str = "generic"  # type of mob for visuals/behavior


@dataclass
class Item:
    name: str
    attack_bonus: int = 0
    defense_bonus: int = 0
    cost: int = 0
    tier: int = 1
    type: str = "melee"  # 'melee' | 'ranged' | 'magic' | 'armor' | 'artifact' | other


@dataclass
class Player(Entity):
    level: int = 1
    crystals: int = 0
    xp: int = 0
    # inventory: fixed size 10 slots
    inventory: List[Optional[Item]] = field(default_factory=lambda: [None] * 10)
    # equipped items (only one per category)
    equipped_melee: Optional[Item] = None
    equipped_ranged: Optional[Item] = None
    equipped_magic: Optional[Item] = None
    equipped_armor: Optional[Item] = None
    equipped_artifact: Optional[Item] = None

    # base stats for recomputation
    base_hp: int = 100
    base_attack: int = 10
    base_defense: int = 5

    max_hp: int = 100

    def __post_init__(self):
        # ensure base stats reflect initial values
        self.base_hp = self.hp
        self.max_hp = self.hp
        self.base_attack = self.attack
        self.base_defense = self.defense

    def equip_direct(self, item: Item):
        """
        Equip an item directly (not necessarily from inventory).
        This places the item into the matching equipped_* slot and recomputes stats.
        """
        if item.type == "melee":
            self.equipped_melee = item
        elif item.type == "ranged":
            self.equipped_ranged = item
        elif item.type == "magic":
            self.equipped_magic = item
        elif item.type == "armor":
            self.equipped_armor = item
        elif item.type == "artifact":
            self.equipped_artifact = item
        else:
            # Unknown type: put into inventory if possible
            self.add_to_inventory(item)
        self.recompute_stats()

    def recompute_stats(self):
        """Recompute attack/defense from base stats + equipped bonuses."""
        atk = self.base_attack
        dfs = self.base_defense
        if self.equipped_melee:
            atk += self.equipped_melee.attack_bonus
            dfs += self.equipped_melee.defense_bonus
        if self.equipped_ranged:
            atk += self.equipped_ranged.attack_bonus
            dfs += self.equipped_ranged.defense_bonus
        if self.equipped_magic:
            atk += self.equipped_magic.attack_bonus
            dfs += self.equipped_magic.defense_bonus
        if self.equipped_armor:
            atk += self.equipped_armor.attack_bonus
            dfs += self.equipped_armor.defense_bonus
        if self.equipped_artifact:
            # artifacts may give small bonuses
            atk += self.equipped_artifact.attack_bonus
            dfs += self.equipped_artifact.defense_bonus
        self.attack = max(1, atk)
        self.defense = max(0, dfs)

    def add_to_inventory(self, item: Item) -> bool:
        """Add item to first empty inventory slot. Return True if placed, False if full."""
        for i in range(len(self.inventory)):
            if self.inventory[i] is None:
                self.inventory[i] = item
                return True
        return False

    def swap_inventory_slot(self, index: int, item: Item) -> Optional[Item]:
        """
        Replace inventory[index] with item and return the replaced item (or None).
        If index out of range, raise IndexError.
        """
        if index < 0 or index >= len(self.inventory):
            raise IndexError("invalid inventory index")
        replaced = self.inventory[index]
        self.inventory[index] = item
        return replaced

    def equip_from_inventory(self, index: int) -> bool:
        """
        Equip the item from inventory[index] into the matching equipped slot.
        If no item or types don't match equip types, return False.
        """
        if index < 0 or index >= len(self.inventory):
            return False
        item = self.inventory[index]
        if item is None:
            return False
        # Determine slot
        if item.type in ("melee", "ranged", "magic", "armor", "artifact"):
            # equip into that slot and remove from inventory (put currently equipped into inventory)
            replaced_equipped = None
            if item.type == "melee":
                replaced_equipped = self.equipped_melee
                self.equipped_melee = item
            elif item.type == "ranged":
                replaced_equipped = self.equipped_ranged
                self.equipped_ranged = item
            elif item.type == "magic":
                replaced_equipped = self.equipped_magic
                self.equipped_magic = item
            elif item.type == "armor":
                replaced_equipped = self.equipped_armor
                self.equipped_armor = item
            elif item.type == "artifact":
                replaced_equipped = self.equipped_artifact
                self.equipped_artifact = item
            # remove from inventory
            self.inventory[index] = None
            # try to place replaced_equipped back into inventory; if no space, drop it (or swap into this index)
            if replaced_equipped is not None:
                placed = self.add_to_inventory(replaced_equipped)
                if not placed:
                    # inventory full: put it back into same index to avoid loss
                    self.inventory[index] = replaced_equipped
                    # undo equip
                    if item.type == "melee":
                        self.equipped_melee = replaced_equipped
                    elif item.type == "ranged":
                        self.equipped_ranged = replaced_equipped
                    elif item.type == "magic":
                        self.equipped_magic = replaced_equipped
                    elif item.type == "armor":
                        self.equipped_armor = replaced_equipped
                    elif item.type == "artifact":
                        self.equipped_artifact = replaced_equipped
                    return False
            self.recompute_stats()
            return True
        return False

    def gain_crystals(self, amount: int):
        self.crystals += amount

    def attack_target(self, target: Entity) -> int:
        base = self.attack
        damage = target.take_damage(base)
        return damage

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    # --- new helper methods expected by GUI ---

    def effective_inventory_size(self) -> int:
        """
        Return the current effective inventory size (number of slots to display).
        Currently fixed to the inventory length; kept as a separate method in case
        artifacts or upgrades later increase capacity.
        """
        return len(self.inventory)

    def clear_inventory_and_equipment(self):
        """
        Clear player's inventory and unequip all items. Recompute stats and reset inventory.
        Called when the player dies (GUI.handle_death).
        """
        self.inventory = [None] * len(self.inventory)
        self.equipped_melee = None
        self.equipped_ranged = None
        self.equipped_magic = None
        self.equipped_armor = None
        self.equipped_artifact = None
        # reset stats to base values based on initial base_*
        self.recompute_stats()


# Class-specific factories for easy creation with different base stats
def create_warrior(name: str = "Warrior") -> Player:
    p = Player(name=name, hp=120, attack=14, defense=6)
    p.base_hp = 120
    p.max_hp = 120
    p.base_attack = 14
    p.base_defense = 6
    p.crystals = 10  # starting crystals
    return p


def create_archer(name: str = "Archer") -> Player:
    p = Player(name=name, hp=90, attack=16, defense=3)
    p.base_hp = 90
    p.max_hp = 90
    p.base_attack = 16
    p.base_defense = 3
    p.crystals = 10
    return p


def create_sorcerer(name: str = "Sorcerer") -> Player:
    p = Player(name=name, hp=75, attack=18, defense=2)
    p.base_hp = 75
    p.max_hp = 75
    p.base_attack = 18
    p.base_defense = 2
    p.crystals = 10
    return p


def create_rogue(name: str = "Rogue") -> Player:
    p = Player(name=name, hp=80, attack=15, defense=3)
    p.base_hp = 80
    p.max_hp = 80
    p.base_attack = 15
    p.base_defense = 3
    p.crystals = 10
    return p


def create_paladin(name: str = "Paladin") -> Player:
    p = Player(name=name, hp=110, attack=13, defense=7)
    p.base_hp = 110
    p.max_hp = 110
    p.base_attack = 13
    p.base_defense = 7
    p.crystals = 10
    return p


def create_necromancer(name: str = "Necromancer") -> Player:
    p = Player(name=name, hp=70, attack=17, defense=2)
    p.base_hp = 70
    p.max_hp = 70
    p.base_attack = 17
    p.base_defense = 2
    p.crystals = 10
    return p