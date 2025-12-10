#!/usr/bin/env python3
"""
Generate simple labeled PNG placeholders (requires Pillow).
Run: python scripts/create_labeled_placeholders.py
Writes images to: src/dungeon_game/assets/images/
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("src/dungeon_game/assets/images")
OUT.mkdir(parents=True, exist_ok=True)

FILES = [
    'weapon_sword.png', 'weapon_bow.png', 'weapon_staff.png', 'weapon_dagger.png', 'weapon_hammer.png',
    'proj_arrow.png', 'proj_magic.png', 'proj_slash.png',
    'mob_slime.png', 'mob_skeleton.png', 'mob_fire.png', 'mob_wolf.png', 'mob_poison.png',
    'player_warrior.png', 'player_archer.png', 'player_sorcerer.png', 'player_rogue.png', 'player_paladin.png', 'player_necromancer.png',
    'arena_forest.png', 'arena_cave.png', 'arena_ruins.png', 'arena_desert.png',
    'ui_shop_panel.png', 'ui_hp_bar.png', 'icon_crystal.png', 'game_icon.png'
]

def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
    """
    Return (width, height) of text using the available Pillow API.
    Tries textbbox (Pillow newer), then textsize, then font.getsize as fallbacks.
    """
    try:
        # Pillow >= 8.0 provides textbbox
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return w, h
    except Exception:
        pass
    try:
        # older method (may not exist on some installs)
        return draw.textsize(text, font=font)
    except Exception:
        pass
    try:
        # final fallback to ImageFont method
        return font.getsize(text)
    except Exception:
        # safe fallback
        return (len(text) * 6, 10)

for name in FILES:
    # choose size depending on asset type
    if 'arena' in name:
        size = (900, 700)
    elif 'proj' in name or 'icon' in name:
        size = (48, 24)
    else:
        size = (128, 128)
    img = Image.new('RGBA', size, (40, 40, 60, 255))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.load_default()
    except Exception:
        f = None
    text = name.replace('.png', '')
    w, h = measure_text(d, text, f)
    d.text(((size[0]-w)/2, (size[1]-h)/2), text, fill=(220,220,220,255), font=f)
    img.save(OUT / name)
    print('Wrote', OUT / name)

print('Done. Replace these PNGs with your real art later.')