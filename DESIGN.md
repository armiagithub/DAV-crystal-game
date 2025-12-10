# Dungeon Game — Design & Roadmap

Purpose
- Quick, modular prototype of a 50-level dungeon roguelike with progression and class differentiation.

Core mechanics
- Levels: 1..50. Each level spawns N mobs where N depends on level and difficulty.
- Mobs: have hp, attack, defense, xp reward, and crystal drop (scaled).
- Player classes:
  - Warrior: high HP, high melee damage, can "block" or "taunt".
  - Archer: medium HP, ranged, chance for critical shots.
  - Sorcerer: low HP, high spell damage, spends mana, can hit multiple mobs.
- Crystals: currency gained from killing mobs. Shops appear at levels 5,10,...50 (every 5 levels).
- Shop: buy weapons/armour or upgrade existing gear. Upgrades increase stats and cost more crystals.
- End of game: can be scoring by total crystals, levels completed, or boss at 50.

Progression and balancing (suggested)
- XP for leveling player: optional (we can use gear-based power instead of player levels).
- Mob HP and damage scale with level by a multiplier: e.g., hp_multiplier = 1 + level * 0.08
- Crystal drop per mob: base_crystal * (1 + level * 0.06)
- Shop item costs scale with level and upgrade tier.

Roadmap (first 2-4 sprints)
1. Sprint 1: Core engine + CLI demo (what you have now)
   - Implement Entities, Level generator, Shop logic, Game orchestrator
   - Basic unit tests for Combat resolution
2. Sprint 2: Persistence + Save/Load + Inventory UI
3. Sprint 3: Add abilities for each class and more item types
4. Sprint 4: Replace CLI with Pygame prototype (movement optional)
5. Sprint 5: Polish, balancing, add boss at level 50 and achievements

Multiplayer notes
- If later you want cooperative play, keep game state deterministic and sync actions via server or peer-to-peer. Start with local multiplayer or hotseat.

Files in scaffold
- src/dungeon_game/*.py: core engine
- README.md, DESIGN.md: documentation

Most if false: all created before finishing