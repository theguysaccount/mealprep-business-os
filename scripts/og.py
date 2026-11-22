"""Render the 1200x630 share card (site/assets/og.png). Needs Pillow; run by hand when the wording changes."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BOLD = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
REG = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def font(cands, size):
    for c in cands:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default(size=size)


img = Image.new("RGB", (1200, 630), (247, 248, 243))
d = ImageDraw.Draw(img)
d.rectangle([0, 0, 1200, 120], fill=(31, 122, 77))
d.text((64, 36), "Meal Prep Business Kit", font=font(BOLD, 46), fill=(255, 255, 255))
d.text((64, 170), "Selling meal prep? Know the rules.", font=font(BOLD, 66), fill=(23, 32, 26))
d.text((64, 262), "Permits for all 50 states + DC, every rule sourced", font=font(REG, 38), fill=(85, 97, 90))
d.text((64, 312), "and dated. Plus a free order page: menu, weekly", font=font(REG, 38), fill=(85, 97, 90))
d.text((64, 362), "cutoff, delivery ZIPs, orders by text. No signup.", font=font(REG, 38), fill=(85, 97, 90))
d.rounded_rectangle([64, 450, 560, 540], radius=18, fill=(242, 177, 52))
d.text((96, 474), "Free, no account", font=font(BOLD, 40), fill=(23, 32, 26))
img.save(ROOT / "site" / "assets" / "og.png", "PNG", optimize=True)
print("site/assets/og.png")
