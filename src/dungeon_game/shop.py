from typing import List, Tuple, Optional
from .entities import Item, Player
import random


class Shop:
    def __init__(self, level_number: int, player_class: str = "warrior"):
        self.level_number = level_number
        self.player_class = player_class
        self.items = self._generate_items_for_level(level_number, player_class)

    def _generate_items_for_level(self, level: int, player_class: str) -> List[Item]:
        # Basic generation: create class-specific items + general items
        base_attack = 2 + level // 5
        base_defense = 1 + level // 6
        items = [
            Item(name=f"Bronze Sword L{level}", attack_bonus=base_attack + 1, defense_bonus=0, cost=5 + level, type="melee"),
            Item(name=f"Leather Armor L{level}", attack_bonus=0, defense_bonus=base_defense + 1, cost=4 + level, type="armor"),
            Item(name=f"Magic Amulet L{level}", attack_bonus=1 + level//10, defense_bonus=1 + level//12, cost=8 + 2*level, type="magic"),
        ]
        # Add class-specific prominent items
        cls = player_class.lower()
        if cls == "warrior" or cls == "paladin":
            items.append(Item(name=f"War Axe L{level}", attack_bonus=base_attack + 3, defense_bonus=0, cost=10 + level, type="melee"))
        if cls == "archer" or cls == "rogue":
            items.append(Item(name=f"Hunter Bow L{level}", attack_bonus=base_attack + 2, defense_bonus=0, cost=9 + level, type="ranged"))
        if cls == "sorcerer" or cls == "necromancer":
            items.append(Item(name=f"Apprentice Staff L{level}", attack_bonus=base_attack + 2, defense_bonus=0, cost=9 + level, type="magic"))
        # add a cheap consumable-like minor item (could be armor or attack)
        items.append(Item(name=f"Sturdy Shield L{level}", attack_bonus=0, defense_bonus=base_defense + 2, cost=6 + level, type="armor"))
        # randomize
        random.shuffle(items)
        return items

    def list_items(self) -> List[Item]:
        return self.items

    def buy(self, player: Player, item_name: str, replace_index: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Attempt to buy item by name.
        - If player has enough crystals and inventory has space: add to inventory and return (True, None)
        - If inventory full and replace_index is None: return (False, "inventory_full")
        - If inventory full and replace_index provided: replace that index and return (True, replaced_item_name)
        - If not enough crystals: (False, "not_enough")
        """
        item = next((it for it in self.items if it.name == item_name), None)
        if item is None:
            return False, "no_item"
        if player.crystals < item.cost:
            return False, "not_enough"
        # spend crystals now (we will give them the item)
        player.crystals -= item.cost
        # try to place in inventory
        placed = player.add_to_inventory(item)
        if placed:
            return True, None
        # inventory full
        if replace_index is None:
            # refund crystals and indicate inventory full
            player.crystals += item.cost
            return False, "inventory_full"
        # perform replacement
        try:
            replaced = player.swap_inventory_slot(replace_index, item)
        except IndexError:
            player.crystals += item.cost
            return False, "invalid_slot"
        replaced_name = replaced.name if replaced else None
        return True, replaced_name