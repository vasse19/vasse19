"""Fast-paced edit of a vertical split-screen podcast clip (MTV Base / Britney / Beyoncé).
Cold open + word captions + speaker-aware reframing + photo B-roll on mentions + 3D cards + SFX."""
import json, sys, subprocess, os, numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from fx3d import text3d

SRC, WORK, OUT = sys.argv[1:4]           # SRC = cut (cold open + full clip)
W, H, FPS = 1080, 1920, 30
CO = 1.6                                  # cold open length; source time t -> cut time t + CO
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC]))
N = int(DUR * FPS); ft = np.arange(N) / FPS

# ---------- transcript (Parakeet + manual fixes cross-checked with Whisper) ----------
head = json.load(open(f"{WORK}/head.json")); body = [w for w in json.load(open(f"{WORK}/words.json")) if w["s"] >= 9.9]
words = head + body
def sub(t0, t1, text):
    global words
    keep = [w for w in words if not (t0 - 0.01 <= w["s"] < t1)]
    new = text.split(); k = len(new)
    words = sorted(keep + [{"w": x, "s": t0 + (t1 - t0) * i / k, "e": 0} for i, x in enumerate(new)], key=lambda w: w["s"])
sub(0.8, 2.3, "je t'ai dit MTV Base là.")
sub(3.2, 4.2, "la chaîne MTV Base ?")
sub(7.9, 9.6, "Sinon avant c'était que de l'anglais, que de l'anglais.")
sub(12.8, 13.05, "MTV,")
sub(14.4, 15.8, "Oui. C'est ça qui m'a fait mal.")
sub(17.0, 19.5, "Ouais mais y a TikTok, y a YouTube. Non, c'est TikTok.")
sub(19.5, 22.2, "")
sub(22.2, 22.9, "les derniers sons...")
sub(38.3, 39.7, "Ça fait polémique ces temps-ci,")
sub(41.7, 41.95, "gérait,")
sub(51.9, 54.0, "Oui, qui géraient aussi les Destiny's Child ou quoi.")
sub(55.3, 55.9, "que sa carrière solo,")
words = [w for w in words if w["w"] not in ("!", "?") and w["w"]]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else 58.2
    w["e"] = min(nxt, w["s"] + 0.6)
cold = [dict(w, s=w["s"] - 12.85, e=w["e"] - 12.85) for w in words if 12.85 <= w["s"] < 14.45]
words = cold + [dict(w, s=w["s"] + CO, e=w["e"] + CO) for w in words]
json.dump(words, open(f"{WORK}/words_final.json", "w"), ensure_ascii=False)
key = lambda w: w["w"].lower().strip(",.?!…")

# ---------- photo B-roll on mentions (cut time) ----------
BROLL = [(0.0, CO, "mtv"), (2.9, 6.0, "mtv"), (25.6, 28.75, "britney"), (46.95, 49.9, "beyonce"), (56.5, DUR, "beyonce")]
def in_broll(t):
    for a, b, n in BROLL:
        if a <= t < b: return (a, b, n)
    return None
def cover(img, w, h):
    s = max(w / img.shape[1], h / img.shape[0]); r = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    y = (r.shape[0] - h) // 2; x = (r.shape[1] - w) // 2
    return r[y:y + h, x:x + w]
def rim(card, px=6):
    c = card.copy(); c[:px] = c[-px:] = c[:, :px] = c[:, -px:] = (66, 197, 245); return c
PH = {}
mtv = cv2.imread(f"{WORK}/mtv-base-logo.png")
bg = np.zeros((H, W, 3), np.uint8); bg[:] = (110, 255, 51)
PH["mtv"] = (bg.astype(np.float32) / 255, cv2.resize(mtv, (760, int(760 * mtv.shape[0] / mtv.shape[1])), interpolation=cv2.INTER_AREA).astype(np.float32) / 255, 700)
for n, f, cw, ch in (("britney", "britney.jpg", 1000, 684), ("beyonce", "beyonce.jpg", 1000, 1000)):
    im = cv2.imread(f"{WORK}/{f}")
    b = cv2.GaussianBlur(cover(im, W, H), (0, 0), 30).astype(np.float32) / 255 * 0.45
    PH[n] = (b, rim(cover(im, cw, ch)).astype(np.float32) / 255, 860)

def broll_frame(t, a, b, n):
    bgi, card, cy = PH[n]; k = t - a
    img = bgi.copy()
    s = (1.14 - 0.14 * min(k / 0.3, 1) ** 0.4) * (1 + 0.04 * (k / (b - a)))       # lands, then slow push
    c = cv2.resize(card, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
    h, w = c.shape[:2]; x0, y0 = (W - w) // 2, cy - h // 2
    xa, ya = max(x0, 0), max(y0, 0); xb, yb = min(x0 + w, W), min(y0 + h, H)
    img[ya:yb, xa:xb] = c[ya - y0:yb - y0, xa - x0:xb - x0]
    if k < 0.07 and a > 0: img = np.clip(img + (0.07 - k) / 0.07 * 0.6, 0, 1)
    return img

# ---------- 3D cards ----------
CARDS = [  # start, end, top, bottom ('|' new line), kind, centre y
    (0.0, CO, "MTV BASE", "C'EST|FINI ?", "hook", 1420),
    (28.75, 30.0, "BRITNEY", "MÉGA|STAR", "card", 960),
    (42.1, 43.15, "PAS", "LIBRE", "card", 960),
    (46.0, 46.95, "CONTRE-|EXEMPLE", "BEYONCÉ", "card", 960),
    (58.3, DUR, "PARTIE 2", "BEYONCÉ", "end", 1380),
]
def block(top, bot, width, maxh):
    lines = [text3d(l, 220, "chrome", 30) for l in top.split("|")] + [text3d(l, 210, "red", 30) for l in bot.split("|")]
    im = Image.new("RGBA", (max(l.width for l in lines) + 40, sum(l.height for l in lines) - 110 * (len(lines) - 1)))
    y = 0
    for l in lines:
        im.alpha_composite(l, ((im.width - l.width) // 2, y)); y += l.height - 110
    im = im.rotate(5, expand=True, resample=Image.BICUBIC)
    sc = min(width / im.width, maxh / im.height)
    return np.asarray(im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)).astype(np.float32) / 255
card_img = [block(c[2], c[3], 1040, 760 if c[4] in ("hook", "end") else 1000) for c in CARDS]
warn = Image.new("RGBA", (220, 200)); d = ImageDraw.Draw(warn)
d.polygon([(110, 6), (214, 194), (6, 194)], fill=(255, 210, 0, 255), outline=(0, 0, 0, 255), width=10)
d.rectangle((100, 60, 120, 140), fill=(0, 0, 0, 255)); d.ellipse((98, 152, 122, 176), fill=(0, 0, 0, 255))
warn = np.asarray(warn).astype(np.float32) / 255
def paste(dst, rgba, cx, cy, scale=1.0):
    if scale != 1.0: rgba = cv2.resize(rgba, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = rgba.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb: return
    src = rgba[ya - y0:yb - y0, xa - x0:xb - x0]; a = src[..., 3:4]
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + src[..., [2, 1, 0]] * a
def in_card(t, full_only=False):
    return any(c[0] <= t < c[1] and (not full_only or c[4] == "card") for c in CARDS)

# ---------- shots: the active speaker sits on top in the source; reframe every ~2.3 s ----------
SWITCH = [CO + t for t in (9.87, 12.0, 15.93, 17.03, 18.57, 34.1, 42.7, 46.57, 47.37, 51.97)]
cuts = [CO]
for w in words:
    if w["s"] < CO: continue
    if (w["w"][-1] in ",.?…" and w["e"] - cuts[-1] > 2.0) or w["s"] - cuts[-1] > 3.0:
        cuts.append(round(w["e"] if w["w"][-1] in ",.?…" else w["s"], 2))
cuts = sorted(set(cuts + SWITCH))
cuts = [c for i, c in enumerate(cuts) if i == 0 or c - cuts[i - 1] > 0.9]
CYCLE = ["TOP", "TOPT", "SPLIT", "TOP", "TOPT", "BOT"]
SHOTS = [(0.0, "TOP")] + [(c, CYCLE[i % len(CYCLE)]) for i, c in enumerate(cuts)]
def shot_at(t):
    m = SHOTS[0][1]
    for s_, mm in SHOTS:
        if t >= s_: m = mm
    return m

# ---------- face tracks (per half) ----------
fc = json.load(open(f"{WORK}/faces.json"))
def track(name):
    a = np.array(fc[name]); t, x = a[:, 0], a[:, 1]
    mx = np.array([np.median(x[(t > tt - 0.7) & (t < tt + 0.7)]) for tt in t])
    k = np.abs(x - mx) < 120; t, x = t[k], x[k]
    xs = np.interp(ft, t, x); ker = np.ones(9) / 9
    return np.convolve(np.pad(xs, 4, mode="edge"), ker, mode="valid")
txc, bxc = track("top"), track("bot")

# ---------- zoom ----------
z = np.ones(N)
def punch(t0, amt, hold=0.3, rel=0.45):
    a = np.clip((ft - t0) / 0.07, 0, 1); a = a * a * (3 - 2 * a)
    r = np.clip((ft - t0 - hold) / rel, 0, 1); r = r * r * (3 - 2 * r)
    return amt * a * (1 - r)
EMPH_RED = {"fini", "fermé", "mal", "méga", "star", "libre", "polémique", "contre-exemple", "continue", "solo"}
EMPH_WHITE = {"mtv", "base", "tiktok", "youtube", "britney", "spears", "beyoncé", "destiny's", "child", "états-unis", "anglais", "français"}
for w in words:
    if key(w) in EMPH_RED: z += punch(w["s"], 0.12)
for c, _ in SHOTS[1:]: z += punch(c - 0.001, 0.07, 0.0, 0.25)
shake = np.zeros((N, 2)); rng = np.random.default_rng(9)
for c in CARDS:
    m = (ft >= c[0]) & (ft < c[0] + 0.3)
    shake[m] = rng.normal(0, 10, (m.sum(), 2)) * np.linspace(1, 0, m.sum())[:, None]

TOP_H, BOT_Y = 905, 1012     # picture bands above / below the source's centre banner
def crop_rect(i):
    m = shot_at(ft[i]); zz = z[i]
    if m == "SPLIT":
        cw, ch = W / zz, H / zz; return 540 - cw / 2, 960 - ch / 2, cw, ch
    if m == "BOT":
        ch = (H - BOT_Y) / zz; cw = ch * W / H; cx = bxc[i]; y0 = BOT_Y + ((H - BOT_Y) - ch) * 0.35
    else:
        ch = (TOP_H if m == "TOP" else 700) / zz; cw = ch * W / H; cx = txc[i]; y0 = (TOP_H - ch) * 0.4
    return np.clip(cx - cw / 2, 0, W - cw), y0, cw, ch

# ---------- captions ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: W,Inter ExtraBold,104,&H0000E5FF,&H0000E5FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,8,5,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
for w in words:
    if in_card(w["s"]): continue
    e = w["e"]
    for c in CARDS:
        if w["s"] < c[0] < e: e = c[0]
    col = r"\c&H002A2AFF&" if key(w) in EMPH_RED else (r"\c&H00FFFFFF&" if key(w) in EMPH_WHITE else "")
    txt = w["w"].upper().rstrip(",.?!…") or w["w"]
    y = 1600 if in_broll(w["s"]) else (960 if shot_at(w["s"]) == "SPLIT" else 1400)
    ass.append(f"Dialogue: 0,{ts(w['s'])},{ts(e)},W,,0,0,0,,{{\\an5\\pos(540,{y}){col}\\fscx72\\fscy72\\t(0,90,\\fscx108\\fscy108)\\t(90,150,\\fscx100\\fscy100)}}{txt}")
open(f"{WORK}/caps.ass", "w").write("\n".join(ass) + "\n")

# ---------- sound design ----------
def synth(args, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", args, "-ac", "1", "-ar", "48000", path], check=True)
    return np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "48000", "-"]), np.float32)
whoosh = synth("anoisesrc=d=0.45:c=pink:a=0.9,highpass=f=600,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.18:d=0.27", f"{WORK}/whoosh.wav")
hit = synth("sine=f=52:d=0.7,volume=1.4,afade=t=out:st=0.05:d=0.65", f"{WORK}/hit.wav")
sfx = np.zeros(int(DUR * 48000) + 48000, np.float32)
def place(snd, t, g):
    i = int(max(t, 0) * 48000); sfx[i:i + len(snd)] += snd[:len(sfx) - i] * g
for c, _ in SHOTS[1:]: place(whoosh, c - 0.2, 0.12)
for a, b, n in BROLL: place(whoosh, a - 0.2, 0.25)
for c in CARDS: place(hit, c[0], 0.5); place(whoosh, c[0] - 0.25, 0.25)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", "-", f"{WORK}/sfx.wav"], input=sfx[:int(DUR * 48000)].tobytes(), check=True)

# ---------- render ----------
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
VF = (f"unsharp=5:5:0.5,eq=contrast=1.06:saturation=1.1,vignette=angle=PI/6,noise=alls=4:allf=t+u,ass={WORK}/caps.ass,format=yuv420p")
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", SRC, "-i", f"{WORK}/sfx.wav", "-filter_complex",
    f"[0:v]{VF}[v];[1:a]loudnorm=I=-14.5:TP=-2:LRA=9[vo];[vo][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.9[a]",
    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
for i in range(N):
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    t = ft[i]
    br = in_broll(t)
    if br:
        img = broll_frame(t, *br)
    else:
        x0, y0, cw, ch = crop_rect(i)
        x0 += shake[i, 0]; y0 += shake[i, 1]
        M = np.array([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
        img = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
        if shot_at(t) == "SPLIT":   # cover the source's static banner; the captions sit on this band
            a0, a1 = int(900 - (z[i] - 1) * 120), int(1022 + (z[i] - 1) * 120)
            img[a0:a1] = img[a0:a1] * 0.12
    for ci, c in enumerate(CARDS):
        if not (c[0] <= t < c[1]): continue
        k = t - c[0]
        if c[4] == "card":
            bgc = cv2.GaussianBlur(img, (0, 0), 22); L = bgc.mean(axis=2, keepdims=True)
            img = np.clip(L * np.array([0.12, 0.12, 0.9]) * 1.3 + bgc * 0.15, 0, 1)
        elif c[4] == "end":
            img = img * 0.55
        if k < 0.07: img = np.clip(img + (0.07 - k) / 0.07 * 0.8, 0, 1)
        s = 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1)
        paste(img, card_img[ci], W / 2 + shake[i, 0], c[5] + shake[i, 1], s)
        if c[4] == "end":
            paste(img, warn, 900, c[5] - 380, min(k / 0.15, 1) * 0.9 + 0.01)
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); dec.wait()
print("done", OUT, len(SHOTS), "shots")
