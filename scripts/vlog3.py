"""Edit a vertical face-cam vlog (Philipayne chronicle): jump cuts, reframing, word captions, logo/photo B-roll on mentions,
3D cards, SFX, loudness to -14 LUFS, CapCut outro removed."""
import json, sys, subprocess, os, numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from fx3d import text3d

SRC, WORK, OUT, LOGO = sys.argv[1:5]
# his library (assets/): copied into the work folder unless a file of that name is already there
import shutil
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
for _n, _p in {'burn.mp4': 'transitions/burn-transition-12.mp4'}.items():
    if not os.path.exists(f"{WORK}/{_n}"): shutil.copy(os.path.join(LIB, _p), f"{WORK}/{_n}")
W, H, FPS = 1080, 1920, 30
END = 86.2                                   # source audio ends at 86.21

# ---------- transcript + fixes (source time) ----------
words = json.load(open(f"{WORK}/words.json"))
def sub(t0, t1, text):
    global words
    keep = [w for w in words if not (t0 - 0.01 <= w["s"] < t1)]
    new = text.split(); k = len(new)
    words = sorted(keep + [{"w": x, "s": t0 + (t1 - t0) * i / k} for i, x in enumerate(new)], key=lambda w: w["s"])
sub(1.55, 2.0, "Philipayne")
sub(4.75, 5.9, "fanbase à lui.")
sub(14.75, 15.1, "Poppa")
sub(15.3, 15.5, "t'as")
sub(16.5, 17.9, "peut créer un univers de malade.")
sub(23.8, 25.0, "son idée à lui,")
sub(30.8, 36.5, "C'est comme si tu partais à la guerre, comme si en gros t'étais un ghost. Si vous avez joué à Call of Duty Black Ops ou sinon Call of Duty Ghost,")
sub(37.5, 38.5, "l'univers de Philipayne,")
sub(44.1, 44.5, "fanbase"); sub(45.1, 45.6, "fanbase"); sub(49.2, 49.7, "fanbase")
sub(54.7, 56.1, "une idée en mode")
sub(56.5, 57.3, "soldats,")
sub(58.9, 59.3, "Gradur,")
sub(63.7, 63.9, "a")
sub(72.0, 72.8, "son délire.")
sub(82.5, 83.3, "Ça, c'est réel.")
sub(83.3, 85.9, "Dites-moi en commentaire. Ciao, peace.")
words = [w for w in words if w["s"] < END]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else END
    est = 0.12 + 0.065 * len(w["w"])            # rough spoken length of the word
    w["e"] = min(nxt, w["s"] + est)

# ---------- edit decision list: drop repeats and filler, cut every silence (jump cuts) ----------
DROP = [(17.98, 21.3),     # second "univers de malade" + an unclear sentence
        (46.3, 47.45),     # "Moi moi je moi"
        (65.7, 66.6),      # "Et non."
        (72.85, 78.4)]     # unclear sentence ("rattaché ... une fois")
def dropped(t): return any(a <= t < b for a, b in DROP)
import soundfile as sf
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-ac", "1", "-ar", "16000", f"{WORK}/edl.wav"], check=True)
au, sr = sf.read(f"{WORK}/edl.wav"); au = au[:int(END * sr)]; hop = int(0.02 * sr)
db = 20 * np.log10(np.array([np.sqrt(np.mean(au[i:i + hop] ** 2)) for i in range(0, len(au) - hop, hop)]) + 1e-9)
db = np.convolve(db, np.ones(3) / 3, mode="same")
keep = db >= np.median(db) - 10                     # speech frames
# a silence shorter than 0.16 s is part of speech; longer ones keep 0.05 s on each side
i = 0
while i < len(keep):
    if not keep[i]:
        j = i
        while j < len(keep) and not keep[j]: j += 1
        if (j - i) * 0.02 < 0.16: keep[i:j] = True
        else: keep[i:i + 3] = True; keep[max(j - 3, i):j] = True
        i = j
    else: i += 1
# the sign-off is spoken softly: keep it whole, from "Ça, c'est réel" to the last frame
keep[int(82.4 / 0.02):] = True
for a0, b0 in DROP: keep[int(a0 / 0.02):int(b0 / 0.02)] = False
runs = []                                           # [first frame, last frame + 1], integer frames
for k, v in enumerate(keep):
    if v:
        if runs and runs[-1][1] == k: runs[-1][1] = k + 1
        else: runs.append([k, k + 1])
segs = [[a0 * 0.02, b0 * 0.02] for a0, b0 in runs if (b0 - a0) * 0.02 >= 0.12]
segs[-1][1] = END
def remap(t):
    acc = 0.0
    for a, b in segs:
        if t < a: return acc
        if t < b: return acc + t - a
        acc += b - a
    return acc
DUR = sum(b - a for a, b in segs)
fc = []
for i, (a, b) in enumerate(segs):
    fc.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{i}]")
fc.append("".join(f"[v{i}][a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[v][a]")
CUT = f"{WORK}/cut.mov"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-r", "30", "-c:a", "pcm_s16le", CUT], check=True)
words = [dict(w, s=remap(w["s"]), e=remap(w["e"])) for w in words if not dropped(w["s"])]
json.dump(words, open(f"{WORK}/words_final.json", "w"), ensure_ascii=False)
print(f"{len(segs)} segments, {DUR:.1f}s (from {END}s)", flush=True)
N = int(DUR * FPS); ft = np.arange(N) / FPS
key = lambda w: w["w"].lower().strip(",.?!…")
def at(text, nth=0): return [w for w in words if key(w) == text][nth]["s"]

# face track on the cut
subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(__file__), "faces_any.py"), CUT, f"{WORK}/faces.json"], check=True, capture_output=True)
f = np.array(json.load(open(f"{WORK}/faces.json")))
fx, fy = np.interp(ft, f[:, 0], f[:, 1]), np.interp(ft, f[:, 0], f[:, 2])
ker = np.ones(15) / 15
sm = lambda v: np.convolve(np.pad(v, 7, mode="edge"), ker, mode="valid")
fx, fy = sm(sm(fx)), sm(sm(fy))
SW, SH = 512, 910

# ---------- B-roll on mentions (cut time) ----------
BROLL = [
    (0.0, at("maintenant"), "artist"),
    (at("virus"), at("ghost"), "virus"),
    (at("ghost"), at("ghost") + 0.8, "ghost"),
    (at("big"), at("big") + 0.8, "bigpoppa"),
    (at("black"), at("franchement"), "blackops"),
    (at("l'univers") - 0.1, at("l'univers") + 1.5, "artist"),
    # Call of Duty footage: the Ghost mask clip on "ghost(s)", the Black Ops trailer on "Black Ops"
    (at("guerre") + 0.55, at("ghost", 1) + 0.26, "vid:ghost:1.0"),
    (at("call") - 0.15, at("sinon"), "vid:blackops:16.6"),
    (at("sinon"), at("l'univers") - 0.1, "vid:ghost:3.0"),
    (at("ghosts") - 0.2, at("ops", 2) - 0.25, "vid:ghost:3.3"),
    (at("ops", 2) - 0.25, at("ops", 2) + 0.85, "vid:blackops:46.6"),
]
VID = {"ghost": f"{WORK}/cod-ghost.mp4", "blackops": f"{WORK}/cod-blackops.mp4"}
VID_VF = {
    # 16:9 clips: the Ghost clip is cropped to a vertical frame around the soldier; the trailer
    # sits full-width over a blurred, darkened copy of itself
    "ghost": f"crop=ih*9/16:ih:iw*0.55-ih*9/32:0,scale={W}:{H}",
    "blackops": f"split[a][b];[a]scale=-2:{H},crop={W}:{H},boxblur=20,eq=brightness=-0.25[bg];[b]scale={W}:-2[fg];[bg][fg]overlay=0:(H-h)/2",
}
_vid = {}
def vid_frame(name, a, b, t):
    """Frame of a footage B-roll span; one decoder per span, read in order."""
    _, clip, src = name.split(":")
    st = _vid.get(name + str(a))
    if st is None:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", src, "-t", f"{b - a + 0.2:.3f}", "-i", VID[clip], "-an",
                              "-filter_complex", VID_VF[clip], "-r", str(FPS), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
        st = _vid[name + str(a)] = {"p": p, "last": None}
    buf = st["p"].stdout.read(W * H * 3)
    if len(buf) == W * H * 3:
        st["last"] = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
    return st["last"]
def in_broll(t):
    for a, b, n in BROLL:
        if a <= t < b: return (a, b, n)
    return None
def cover(img, w, h):
    s = max(w / img.shape[1], h / img.shape[0]); r = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    y = (r.shape[0] - h) // 2; x = (r.shape[1] - w) // 2
    return r[y:y + h, x:x + w]
def solid(bgr):
    b = np.zeros((H, W, 3), np.float32); b[:] = np.array(bgr, np.float32) / 255; return b
def rgba(path, width):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED); s = width / im.shape[1]
    im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return im[..., [2, 1, 0, 3]]                      # to RGBA order used by paste()
def card_layer(path, width):
    im = cv2.imread(path)
    bg = cv2.GaussianBlur(cover(im, W, H), (0, 0), 28).astype(np.float32) / 255 * 0.45
    s_ = width / im.shape[1]
    c = cv2.resize(im, None, fx=s_, fy=s_, interpolation=cv2.INTER_LANCZOS4)
    c = cv2.addWeighted(c, 1.4, cv2.GaussianBlur(c, (0, 0), 2), -0.4, 0)    # mild sharpen after the upscale
    c[:6] = c[-6:] = c[:, :6] = c[:, -6:] = (66, 197, 245)
    return bg, np.dstack([c[..., ::-1].astype(np.float32) / 255, np.ones(c.shape[:2], np.float32)]), 860
PH = {
    "artist": card_layer(f"{WORK}/artist.jpg", 720),
    "virus": card_layer(f"{WORK}/cover-virus.jpg", 900),
    "ghost": card_layer(f"{WORK}/cover-ghost.jpg", 840),
    "bigpoppa": card_layer(f"{WORK}/cover-bigpoppa.jpg", 780),
    "blackops": card_layer(f"{WORK}/cover-blackops.jpg", 940),
}

# ---------- cards ----------
CARDS = [  # start, end, top, bottom, kind, centre y
    (0.0, at("maintenant"), "PHILIPAYNE", "SES FANS =|LES GHOSTS ?", "hook", 1450),
    (at("créer", 1) - 0.1, at("malade") + 0.5, "UN UNIVERS", "DE MALADE", "card", 960),
    (at("guerre") - 0.6, at("guerre") + 0.55, "COMME À", "LA GUERRE", "card", 960),
    (at("call"), at("ghost", 2) + 0.4, "CALL OF DUTY", "BLACK OPS|GHOST", "over", 1420),
    (at("ghosts") - 0.4, at("ops", 2) + 0.5, "LES GHOSTS", "OU LES|BLACK OPS ?", "over", 1420),
    (at("gradur") - 0.25, at("gradur") + 0.75, "À LA", "GRADUR", "card", 960),
    (at("deux") - 0.05, at("année") + 0.4, "2 PROJETS", "EN 1 AN", "card", 960),
    (at("dites-moi") - 0.1, DUR, "LE BIG", "VASS", "end", 1370),
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
card_img = [block(c[2], c[3], 1040, {"hook": 700, "end": 700, "over": 600}.get(c[4], 1000)) for c in CARDS]
logo = rgba(LOGO, 640)
def paste(dst, img, cx, cy, scale=1.0):
    if scale != 1.0: img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = img.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb: return
    src = img[ya - y0:yb - y0, xa - x0:xb - x0]; a = src[..., 3:4]
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + src[..., [2, 1, 0]] * a
def in_card(t): return any(c[0] <= t < c[1] for c in CARDS)

# ---------- shots ----------
cuts = [0.0]
for w in words:
    if (w["w"][-1] in ",.?" and w["e"] - cuts[-1] > 2.0) or w["s"] - cuts[-1] > 3.2:
        cuts.append(round(w["e"] if w["w"][-1] in ",.?" else w["s"], 2))
CYCLE = ["MED", "TIGHT", "WIDE", "TIGHT"]
SHOTS = [(c, CYCLE[i % 4]) for i, c in enumerate(cuts)]
def shot_at(t):
    m = SHOTS[0][1]
    for s_, mm in SHOTS:
        if t >= s_: m = mm
    return m
z = np.ones(N)
def punch(t0, amt, hold=0.3, rel=0.45):
    a = np.clip((ft - t0) / 0.07, 0, 1); a = a * a * (3 - 2 * a)
    r = np.clip((ft - t0 - hold) / rel, 0, 1); r = r * r * (3 - 2 * r)
    return amt * a * (1 - r)
EMPH_RED = {"univers", "malade", "guerre", "fanbase", "militaire", "soldats", "dingueries", "étape", "capitaliser", "délire", "réel"}
EMPH_WHITE = {"philipayne", "virus", "ghost", "big", "poppa", "black", "ops", "call", "duty", "ghosts", "gradur", "projets"}
for w in words:
    if key(w) in EMPH_RED: z += punch(w["s"], 0.1)
for c, _ in SHOTS[1:]: z += punch(c - 0.001, 0.06, 0.0, 0.25)
shake = np.zeros((N, 2)); rng = np.random.default_rng(4)
for c in CARDS:
    m = (ft >= c[0]) & (ft < c[0] + 0.3)
    shake[m] = rng.normal(0, 10, (m.sum(), 2)) * np.linspace(1, 0, m.sum())[:, None]
def crop_rect(i):
    zz = z[i] * {"WIDE": 1.0, "MED": 1.15, "TIGHT": 1.32}[shot_at(ft[i])]
    ch = SH / zz; cw = ch * W / H
    return np.clip(fx[i] - cw / 2, 0, SW - cw), np.clip(fy[i] - ch * 0.4, 0, SH - ch), cw, ch

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
    y = 1620 if in_broll(w["s"]) else 1420
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
for c, _ in SHOTS[1:]: place(whoosh, c - 0.2, 0.1)
for a, b, n in BROLL: place(whoosh, a - 0.2, 0.25)
for c in CARDS: place(hit, c[0], 0.45); place(whoosh, c[0] - 0.25, 0.22)
BURN_AT = [at("maintenant"), at("virus"), at("guerre") - 0.6, at("ghosts") - 0.4, at("dites-moi") - 0.1]
burn_snd = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", f"{WORK}/burn.mp4", "-f", "f32le", "-ac", "1", "-ar", "48000", "-"]), np.float32)
for b_ in BURN_AT: place(burn_snd, b_ - 0.39, 0.7)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", "-", f"{WORK}/sfx.wav"], input=sfx[:int(DUR * 48000)].tobytes(), check=True)

# ---------- render ----------
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", CUT, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
VF = f"unsharp=5:5:0.5,eq=contrast=1.06:saturation=1.08,vignette=angle=PI/6,noise=alls=3:allf=t+u,ass={WORK}/caps.ass,format=yuv420p"
# picture only here: mixing the audio in the same process as the piped frames can deadlock
VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-vf", VF, "-c:v", "libx264", "-preset", "medium", "-crf", "19", VIDEO_ONLY], stdin=subprocess.PIPE)
bdec = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{WORK}/burn.mp4", "-vf", f"scale=-2:{H},crop={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
BURN = np.frombuffer(bdec, np.uint8).reshape(-1, H, W, 3)
FR = SW * SH * 3
for i in range(N):
    buf = dec.stdout.read(FR)
    if len(buf) < FR: break
    fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3); t = ft[i]
    br = in_broll(t)
    if br and br[2].startswith("vid:"):
        a, b, n = br
        img = vid_frame(n, a, b, t).copy()
        if t - a < 0.07: img = np.clip(img + (0.07 - (t - a)) / 0.07 * 0.5, 0, 1)
    elif br:
        a, b, n = br; bgi, card, cy = PH[n]; k = t - a
        img = bgi.copy()
        s = (1.14 - 0.14 * min(k / 0.3, 1) ** 0.4) * (1 + 0.04 * k / (b - a))
        paste(img, card, W / 2, cy, s)
        if k < 0.07: img = np.clip(img + (0.07 - k) / 0.07 * 0.6, 0, 1)
    else:
        x0, y0, cw, ch = crop_rect(i)
        x0 += shake[i, 0] * cw / W; y0 += shake[i, 1] * ch / H
        M = np.array([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
        img = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
    for ci, c in enumerate(CARDS):
        if not (c[0] <= t < c[1]): continue
        k = t - c[0]
        if c[4] == "card":
            bgc = cv2.GaussianBlur(img, (0, 0), 22); L = bgc.mean(axis=2, keepdims=True)
            img = np.clip(L * np.array([0.12, 0.12, 0.9]) * 1.3 + bgc * 0.15, 0, 1)
        elif c[4] == "end":
            img = img * 0.45
        elif c[4] == "hook":
            img = img * (1 - 0.35 * min(k / 0.2, 1))
        if k < 0.07: img = np.clip(img + (0.07 - k) / 0.07 * 0.8, 0, 1)
        s = 0.55 + 0.55 * min(k / 0.12, 1) - 0.1 * min(max(k - 0.12, 0) / 0.1, 1)
        if c[4] == "end":
            paste(img, logo, W / 2, 700, min(k / 0.25, 1) * 0.15 + 0.85)
        paste(img, card_img[ci], W / 2 + shake[i, 0], c[5] + shake[i, 1], s)
    for b_ in BURN_AT:
        k = int(round((t - (b_ - 0.39)) * FPS))
        if 0 <= k < len(BURN):
            img = 1 - (1 - img) * (1 - BURN[k].astype(np.float32) / 255)       # screen blend
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()
dec.stdout.close(); dec.kill(); dec.wait()   # the decoder may still hold a frame or two past N
# voice: very quiet source, so gain, then light compression, then loudness to about -14 LUFS
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-i", CUT, "-i", f"{WORK}/sfx.wav", "-filter_complex",
    # loudnorm runs at 192 kHz internally: resample and re-stamp before amix, or the voice drops out at the end
    "[1:a]highpass=f=70,volume=11dB,acompressor=threshold=-22dB:ratio=4:attack=5:release=90:makeup=3dB,loudnorm=I=-14:TP=-1.5:LRA=7,"
    "aresample=48000,asetpts=N/SR/TB[vo];[2:a]aresample=48000,asetpts=N/SR/TB[fx];"
    "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.75:level=false[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, len(SHOTS), "shots", flush=True)
