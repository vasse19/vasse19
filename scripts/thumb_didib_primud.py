"""YouTube thumbnail 1280x720: « DIDI B ABSENT DES PRIMUD : BOYCOTT OU SIMPLE CHOIX ? » from his own images.
Left: Didi B photo as a tilted glowing card on red/black; right: PRIMUD 11 logo on emerald green with a red « ABSENT » stamp;
centre: golden house key (the house never received); 3D title « BOYCOTT ? »; Monsieur Vass logo top-left.
usage: thumb_didib_primud.py IMG_DIR OUT.jpg"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import block, ANTON

IMG, OUT = sys.argv[1:3]
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H = 1280, 720
yy, xx = np.mgrid[:H, :W].astype(np.float32)

# background: red/black left, emerald right, split by a glowing diagonal crack
red = np.dstack([0.55 - 0.45 * xx / W, 0.02 + 0 * xx, 0.04 + 0 * xx]) * (1.1 - 0.6 * yy / H)[..., None]
green = np.dstack([0.0 + 0 * xx, 0.20 + 0.12 * (1 - yy / H), 0.14 + 0.06 * (1 - yy / H)])
split = 600 + (yy - H / 2) * 0.35
m = np.clip((xx - split) / 30 + 0.5, 0, 1)[..., None]
bg = red * (1 - m) + green * m
crack = np.exp(-((xx - split) / 6) ** 2)[..., None] * np.array([1.0, 0.8, 0.3])
glow = np.exp(-((xx - split) / 40) ** 2)[..., None] * np.array([1.0, 0.65, 0.2]) * 0.6
vig = np.clip(1.25 - np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 1.3, 0.3, 1)[..., None]
rng = np.random.default_rng(3)
sparks = np.zeros((H, W), np.float32)
for _ in range(260):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    cv2.circle(sparks, (int(x), int(y)), int(rng.uniform(1, 3)), float(rng.uniform(0.4, 1)), -1, cv2.LINE_AA)
sparks = cv2.GaussianBlur(sparks, (0, 0), 1.2)[..., None] * np.array([1.0, 0.75, 0.3])
canvas = np.clip((bg + crack + glow) * vig + sparks * 0.8, 0, 1)
img = Image.fromarray((canvas * 255).astype(np.uint8)).convert("RGBA")

def glow_card(path, height, rim, angle, border=8):
    ph = Image.open(path).convert("RGB"); s = height / ph.height
    ph = ph.resize((int(ph.width * s), height), Image.LANCZOS)
    c = Image.new("RGBA", (ph.width + 2 * border, ph.height + 2 * border), rim + (255,)); c.paste(ph, (border, border))
    c = c.rotate(angle, expand=True, resample=Image.BICUBIC)
    pad = 60; g = Image.new("RGBA", (c.width + 2 * pad, c.height + 2 * pad))
    a = Image.new("L", g.size); a.paste(c.split()[3], (pad, pad)); a = a.filter(ImageFilter.GaussianBlur(22))
    g.paste(Image.new("RGBA", g.size, rim + (255,)), (0, 0), a.point(lambda v: min(255, int(v * 1.6))))
    g.alpha_composite(c, (pad, pad)); return g

# Didi B (his photo), left
didi = glow_card(f"{IMG}/didib-plateau.jpg", 560, (255, 255, 255), 4)
img.alpha_composite(didi, (40 - 60, 110 - 60))

# PRIMUD 11 logo (gold on green, cropped), right, with « ABSENT » stamp
logo = Image.open(f"{IMG}/logo-primud-11.jpg").convert("RGB"); lw = logo.width
logo = logo.crop((int(lw * 0.27), int(lw * 0.18), int(lw * 0.73), int(lw * 0.82))).resize((300, 418), Image.LANCZOS)
lg = glow_card.__wrapped__ if hasattr(glow_card, "__wrapped__") else None
tmp = f"{IMG}/_logo_crop.jpg"; logo.save(tmp, quality=95)
lc = glow_card(tmp, 360, (255, 200, 70), -4)
img.alpha_composite(lc, (900 - 60, 300 - 60))
st = Image.new("RGBA", (420, 130)); d = ImageDraw.Draw(st); f = ImageFont.truetype(ANTON, 96)
d.rounded_rectangle((6, 6, 414, 124), 10, outline=(235, 30, 40, 255), width=10)
bb = d.textbbox((0, 0), "ABSENT", font=f); d.text(((420 - bb[2] + bb[0]) / 2 - bb[0], (130 - bb[3] + bb[1]) / 2 - bb[1]), "ABSENT", font=f, fill=(235, 30, 40, 255))
st = st.rotate(-14, expand=True, resample=Image.BICUBIC)
img.alpha_composite(st, (845, 480))

# golden key (the house), centre
ef = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
ke = Image.new("RGBA", (160, 160)); ImageDraw.Draw(ke).text((20, 15), "🔑", font=ef, embedded_color=True)
ke = ke.crop(ke.getbbox()).resize((190, 190), Image.LANCZOS).rotate(-20, expand=True, resample=Image.BICUBIC)
kg = Image.new("RGBA", (ke.width + 80, ke.height + 80)); a = Image.new("L", kg.size); a.paste(ke.split()[3], (40, 40))
kg.paste(Image.new("RGBA", kg.size, (255, 200, 60, 255)), (0, 0), a.filter(ImageFilter.GaussianBlur(18)).point(lambda v: min(255, v * 2)))
kg.alpha_composite(ke, (40, 40)); img.alpha_composite(kg, (560, 420))

# 3D title, top-right
t = block("BOYCOTT", "OU CHOIX ?", 640, 300)
ti = Image.fromarray((t * 255).astype(np.uint8), "RGBA"); img.alpha_composite(ti, (W - ti.width - 20, 0))

# Monsieur Vass logo, top-left
lv = Image.open(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png")).convert("RGBA"); s = 120 / lv.width
lv = lv.resize((120, int(lv.height * s)), Image.LANCZOS); img.alpha_composite(lv, (18, 14))

img.convert("RGB").save(OUT, quality=95); os.remove(tmp); print("done", OUT)
