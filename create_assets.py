from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def gradient(size, top, bottom):
    w, h = size
    image = Image.new("RGB", size)
    px = image.load()
    for y in range(h):
        t = y / max(1, h - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(w):
            px[x, y] = color
    return image


def draw_atom(draw: ImageDraw.ImageDraw, center, scale: float, line=(190, 204, 255), nucleus=(139, 140, 255)):
    cx, cy = center
    r = max(2, int(8 * scale))
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=nucleus, outline=(235, 255, 251), width=max(1, int(scale)))
    boxes = [
        (cx-43*scale, cy-15*scale, cx+43*scale, cy+15*scale, 8),
        (cx-27*scale, cy-35*scale, cx+27*scale, cy+35*scale, 53),
        (cx-30*scale, cy-33*scale, cx+30*scale, cy+33*scale, 127),
    ]
    for x1, y1, x2, y2, rot in boxes:
        layer = Image.new("RGBA", draw._image.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.ellipse((x1, y1, x2, y2), outline=line + (255,), width=max(1, int(2*scale)))
        if rot:
            layer = layer.rotate(rot, center=(cx, cy), resample=Image.Resampling.BICUBIC)
        draw._image.alpha_composite(layer) if draw._image.mode == "RGBA" else draw._image.paste(layer, (0, 0), layer)


def make_icon():
    # Original icon: layered rounded tile + orbit mark. Inspired by modern
    # platform design principles, not copied from any vendor icon.
    im = Image.new("RGBA", (256, 256), (18, 19, 29, 255))
    d = ImageDraw.Draw(im)
    for y in range(256):
        t = y / 255
        c = (int(36 + 28*t), int(38 + 17*t), int(88 + 54*t), 255)
        d.line((0, y, 255, y), fill=c)
    d.rounded_rectangle((18, 18, 238, 238), radius=58, fill=(26, 27, 42, 235), outline=(156, 159, 255), width=4)
    # soft accent disks
    d.ellipse((130, -18, 280, 132), fill=(85, 90, 206, 120))
    d.ellipse((-30, 120, 130, 280), fill=(98, 63, 151, 100))
    draw_atom(d, (128, 111), 1.58, line=(190, 204, 255), nucleus=(139, 140, 255))
    d.rounded_rectangle((74, 172, 182, 212), radius=20, fill=(244, 244, 252, 235))
    d.text((128, 192), "P+M", anchor="mm", fill=(48, 49, 75), font=font(26, True))
    im.save(ASSETS / "physics_pocket.png")
    im.save(ASSETS / "physics_pocket.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])


def make_wizard():
    base = gradient((164, 314), (18, 19, 29), (46, 43, 90)).convert("RGBA")
    d = ImageDraw.Draw(base)
    # stars / particles
    for i in range(70):
        x = (i * 47 + 19) % 160
        y = (i * 83 + 13) % 300
        r = 1 if i % 5 else 2
        d.ellipse((x-r, y-r, x+r, y+r), fill=(122, 210, 204, 150))
    d.rounded_rectangle((12, 12, 152, 302), radius=18, outline=(139, 140, 255, 210), width=2)
    draw_atom(d, (82, 92), 1.15)
    d.text((82, 171), "PHYSICS", anchor="mm", fill=(241, 255, 252), font=font(18, True))
    d.text((82, 194), "POCKET", anchor="mm", fill=(241, 255, 252), font=font(18, True))
    d.line((37, 216, 127, 216), fill=(139, 140, 255), width=2)
    d.text((82, 239), "SEAMLESS UPDATE", anchor="mm", fill=(150, 239, 221), font=font(10, True))
    d.text((82, 257), "PHYSICS DICTIONARY", anchor="mm", fill=(180, 215, 211), font=font(8))
    d.text((82, 286), "3.1.5", anchor="mm", fill=(235, 255, 251), font=font(12, True))
    base.convert("RGB").save(ASSETS / "wizard.bmp")

    small = gradient((55, 58), (6, 31, 34), (10, 80, 72)).convert("RGBA")
    sd = ImageDraw.Draw(small)
    sd.rounded_rectangle((2, 2, 52, 55), radius=10, outline=(139, 140, 255), width=2)
    draw_atom(sd, (27, 27), 0.48)
    sd.text((27, 47), "PP", anchor="mm", fill=(241, 255, 252), font=font(10, True))
    small.convert("RGB").save(ASSETS / "wizard_small.bmp")


if __name__ == "__main__":
    make_icon()
    make_wizard()
    print("Assets generated in", ASSETS)
