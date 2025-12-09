from typing import List
from .entities import Item, Player


class Shop:
    def __init__(self, level_number: int):
        self.level_number = level_number
        self.items = self._generate_items_for_level(level_number)

    def _generate_items_for_level(self, level: int) -> List[Item]:
        base_attack = 2 + level // 5
        base_defense = 1 + level // 6
        # three sample items
        return [
            Item(name=f"Bronze Sword L{level}", attack_bonus=base_attack, defense_bonus=0, cost=5 + level),
            Item(name=f"Leather Armor L{level}", attack_bonus=0, defense_bonus=base_defense, cost=4 + level),
            Item(name=f"Magic Amulet L{level}", attack_bonus=1 + level//10, defense_bonus=1 + level//12, cost=8 + 2*level),
        ]

    def list_items(self) -> List[Item]:
        return self.items

    def buy(self, player: Player, item_name: str) -> bool:
        item = next((it for it in self.items if it.name == item_name), None)
        if item is None:
            return False
        if player.crystals < item.cost:
            return False
        # Spend crystals and equip
        player.crystals -= item.cost
        player.equip(item)
        return True