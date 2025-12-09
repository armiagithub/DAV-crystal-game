"""
Small CLI demo launcher (kept separate so the gui module can import main without running CLI).
"""
from .entities import create_warrior, create_archer, create_sorcerer
from .game import Game
import sys

def choose_class() -> str:
    print("Choose your class (warrior, archer, sorcerer). Press Enter for 'warrior'.")
    c = input("> ").strip().lower()
    return c or "warrior"

def main():
    print("Dungeon prototype CLI demo")
    choice = choose_class()
    name = input("Enter your name (optional): ").strip() or choice.capitalize()
    player = Game.create_player_by_class(choice, name)
    game = Game(player, max_levels=12)  # demo 12 levels
    print(f"Starting demo with {player.name} ({choice}) - HP: {player.hp}, ATK: {player.attack}, DEF: {player.defense}")

    for lvl in range(1, game.max_levels + 1):
        if not player.is_alive():
            print("You died. Demo ended.")
            break
        print(f"\n--- Level {lvl} ---")
        res = game.run_level(lvl, player_count=1)
        print(f"Kills: {res['kills']}, Crystals gained this level: {res['crystals_gained']}, Total crystals: {res['player_crystals']}, Player HP: {res['player_hp']}")
        if lvl % 5 == 0:
            shop = game.open_shop_if_needed(lvl)
            if shop:
                print("\nShop opened!")
                items = shop.list_items()
                for i, it in enumerate(items, 1):
                    print(f"{i}. {it.name} (ATK+{it.attack_bonus}, DEF+{it.defense_bonus}) - Cost: {it.cost}")
                print("Enter item number to buy or press Enter to skip:")
                choice = input("> ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(items):
                        item = items[idx]
                        bought = shop.buy(player, item.name)
                        if bought:
                            print(f"Bought {item.name}. New ATK: {player.attack}, DEF: {player.defense}, Crystals left: {player.crystals}")
                        else:
                            print("Not enough crystals or error buying item.")
    print("\nDemo finished. History:")
    for entry in game.history:
        print(entry)

if __name__ == "__main__":
    main()