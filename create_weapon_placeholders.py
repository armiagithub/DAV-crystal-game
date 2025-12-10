#!/usr/bin/env python3
"""
Create simple 3-frame weapon animation placeholders.
Requires Pillow:
  python -m pip install --user Pillow

Run:
  python scripts/create_weapon_placeholders.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("src/dungeon_game/assets/images")
OUT.mkdir(parents=True, exist_ok=True)

weapons = {
    "sword": (64,64,'#d66'),
    "bow":   (64,64,'#6d6'),
    "staff": (64,64,'#66d'),
    "dagger":(48,48,'#dd6'),
    "hammer":(64,64,'#d6d'),
}

for name, (w,h,color) in weapons.items():
    for i in range(3):
        img = Image.new('RGBA', (w,h), (30,30,40,255))
        d = ImageDraw.Draw(img)
        # simple moving shape to hint animation
        cx = w//2 + (i-1)*6
        cy = h//2
        r = min(w,h)//4
        d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=color)
        # small slash/streak to show motion
        d.line((w//2, h//2, cx + r + 8, cy - r - 8), fill=(240,240,240), width=2)
        try:
            f = ImageFont.load_default()
        except Exception:
            f = None
        text = f"{name}_{i}"
        tw, th = d.textsize(text, font=f)
        d.text((w- tw - 4, h- th - 2), text, fill=(220,220,220), font=f)
        out = OUT / f"weapon_{name}_anim_{i}.png"
        img.save(out)
        print("Wrote", out)

print("Weapon animation placeholders created. Replace with your art later.")