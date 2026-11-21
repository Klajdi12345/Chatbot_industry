"""Krijon ikonën e FarmaBot-it: flluskë bisede me kapsulë dhe yll AI.
Nxjerr ikona.png (512), logo.png (384x96) dhe farmabot.ico (16–256).   python assets/krijo_ikonen.py"""
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

DIR = Path(__file__).parent
S = 2048  # vizatohet 4x më e madhe dhe zvogëlohet (skaje të buta)


def gradient(w, h, c1, c2, kendi=135):
    """Gradient linear diagonal nga c1 në c2."""
    a = math.radians(kendi)
    dx, dy = math.cos(a), math.sin(a)
    vog = Image.new("RGB", (256, 256))
    px = vog.load()
    for y in range(256):
        for x in range(256):
            t = ((x / 255 - .5) * dx + (y / 255 - .5) * dy) / (abs(dx) + abs(dy)) * 2 * .5 + .5
            t = min(1, max(0, t))
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return vog.resize((w, h), Image.BICUBIC)


def maske_rrumbullake(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def yll(d: ImageDraw.ImageDraw, cx, cy, r, ngjyra):
    """Yll me katër cepa (simboli i AI-së)."""
    pikat = []
    for i in range(8):
        k = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * .28
        pikat.append((cx + rr * math.cos(k), cy + rr * math.sin(k)))
    d.polygon(pikat, fill=ngjyra)


def kapsula(cx, cy, gjat, gjer, kendi, c_majtas, c_djathtas):
    """Kapsulë dyngjyrëshe e rrotulluar, si shtresë RGBA."""
    w, h = int(gjat), int(gjer)
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=c_djathtas)
    gjysma = Image.new("L", (w, h), 0)
    ImageDraw.Draw(gjysma).rectangle((0, 0, w // 2, h), fill=255)
    forma = Image.new("L", (w, h), 0)
    ImageDraw.Draw(forma).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=255)
    majtas = Image.new("RGBA", (w, h), c_majtas)
    sh.paste(majtas, (0, 0), ImageChops.multiply(gjysma, forma))
    # shkëlqim i lehtë sipër
    dr = ImageDraw.Draw(sh)
    dr.rounded_rectangle((h * .35, h * .18, w - h * .35, h * .34), h * .08, fill=(255, 255, 255, 90))
    sh = sh.rotate(kendi, resample=Image.BICUBIC, expand=True)
    return sh, (int(cx - sh.width / 2), int(cy - sh.height / 2))


def ikona() -> Image.Image:
    rad = int(S * .23)
    sfondi = gradient(S, S, (16, 185, 129), (14, 76, 146))
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(sfondi, (0, 0), maske_rrumbullake(S, S, rad))

    # dritë e butë në cepin lart-majtas
    drite = Image.new("L", (S, S), 0)
    ImageDraw.Draw(drite).ellipse((-S * .35, -S * .45, S * .75, S * .55), fill=40)
    drite = drite.filter(ImageFilter.GaussianBlur(S * .08))
    drite = ImageChops.multiply(drite, maske_rrumbullake(S, S, rad))
    img = Image.composite(Image.new("RGBA", (S, S), (255, 255, 255, 255)), img, drite)
    img.putalpha(maske_rrumbullake(S, S, rad))

    # hije e flluskës
    x0, y0, x1, y1 = S * .17, S * .2, S * .83, S * .7
    hije = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hije)
    hd.rounded_rectangle((x0, y0 + S * .03, x1, y1 + S * .03), S * .16, fill=(4, 30, 60, 110))
    hd.polygon([(S * .3, y1 + S * .02), (S * .26, S * .84), (S * .45, y1 + S * .02)], fill=(4, 30, 60, 110))
    hije = hije.filter(ImageFilter.GaussianBlur(S * .025))
    img = Image.alpha_composite(img, hije)

    # flluska e bisedës
    d = ImageDraw.Draw(img)
    bardhe = (255, 255, 255, 255)
    d.rounded_rectangle((x0, y0, x1, y1), S * .16, fill=bardhe)
    d.polygon([(S * .29, y1 - S * .02), (S * .25, S * .81), (S * .44, y1 - S * .02)], fill=bardhe)

    # kapsula
    sh, poz = kapsula(S * .5, S * .45, S * .46, S * .18, 32, (16, 163, 127, 255), (14, 76, 146, 255))
    img.alpha_composite(sh, poz)

    # yjet e AI-së
    yll(d, S * .8, S * .2, S * .1, (255, 200, 87, 255))
    yll(d, S * .9, S * .34, S * .045, (255, 228, 160, 255))
    return img


def ruaj():
    madhe = ikona()
    ik = madhe.resize((512, 512), Image.LANCZOS)
    ik.save(DIR / "ikona.png")
    madhe.resize((256, 256), Image.LANCZOS).save(
        DIR / "farmabot.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    # logo: ikona + "FarmaBot" ("Bot" me ngjyrë)
    L = 4
    logo = Image.new("RGBA", (384 * L, 96 * L), (0, 0, 0, 0))
    logo.alpha_composite(madhe.resize((80 * L, 80 * L), Image.LANCZOS), (8 * L, 8 * L))
    try:
        shkronja = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 46 * L)
    except OSError:
        shkronja = ImageFont.load_default(46 * L)
    d = ImageDraw.Draw(logo)
    y = 48 * L
    d.text((104 * L, y), "Farma", font=shkronja, fill=(15, 23, 42, 255), anchor="lm")
    w = d.textlength("Farma", font=shkronja)
    d.text((104 * L + w, y), "Bot", font=shkronja, fill=(13, 148, 136, 255), anchor="lm")
    logo.resize((384, 96), Image.LANCZOS).save(DIR / "logo.png")


if __name__ == "__main__":
    ruaj()
    print("Ikonat u krijuan te", DIR)
