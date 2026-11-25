"""« 2 millions de streams » proof Short — « Party », Didi B feat. Davido (adapted from proof_2m_youtube.py:
square-ish TikTok repost 576x720 with black bars, Spotify card, streams instead of views).
Original: « 2 millions de vues » proof Short (vertical, Louaista video-essay × Kali): his iPhone screen recording of the clip
(recorded lying down: rotated back with transpose=1), cold open on the clip, then the proof — the clip playing in a
tilted YouTube-style frame on his red/black grid background and a card whose counter runs up to 2 000 000 views —
then back to the clip. His logo top left on every frame. The clip's own sound runs the whole way (as recorded,
limiter only), with his library SFX (hit, whooshes, burn, money counter, cash ding).
usage: proof_2m_spotify.py REC.mp4 OUT.mp4 [title] [subtitle]"""
import sys, os, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kali_fx import LIB, YEL, RED, WHT, GOLD, neon, glow_rgba, block, rgba_file
from proof_fx import Canvas, ease, popk, make_card, draw_stream_card

REC, OUT = sys.argv[1:3]
TITLE = sys.argv[3] if len(sys.argv) > 3 else "LE CLIP"
SUB = sys.argv[4] if len(sys.argv) > 4 else "CLIP OFFICIEL"
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H, FPS, SR = 1080, 1920, 30, 48000
T0 = 0.3
T_PROOF, T_BACK, END = 3.0, 9.6, 17.0
WORK = os.path.dirname(os.path.abspath(OUT))
cv = Canvas(W, H)

# the clip, upright, 1280x720 (source time = T0 + output time)
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(T0), "-t", str(END + 0.2), "-i", REC, "-an", "-vf",
                      f"crop=576:604:0:58,fps={FPS},scale=720:756:flags=lanczos,eq=contrast=1.05:saturation=1.1",
                      "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
CLIP = np.frombuffer(raw, np.uint8).reshape(-1, 756, 720, 3)
def clip(t): return CLIP[min(int(t * FPS), len(CLIP) - 1)].astype(np.float32) / 255

def full(t):
    """Clip filling the vertical frame: blurred copy behind, sharp square-ish band full width."""
    f = clip(t)
    bgi = cv2.resize(cv2.GaussianBlur(cv2.resize(f, (90, 160)), (0, 0), 4), (W, H)) * 0.45
    band = cv2.resize(f, (W, int(W * 756 / 720)), interpolation=cv2.INTER_CUBIC); y0 = (H - band.shape[0]) // 2 - 40
    img = bgi.copy(); img[y0:y0 + band.shape[0]] = band; return img

# cover for the card: the shot in the boubou
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "39.5", "-i", REC, "-frames:v", "1", "-vf", "crop=576:604:0:58", f"{WORK}/cover.jpg"], check=True)
CARD = make_card(f"{WORK}/cover.jpg", TITLE, SUB, "SPOTIFY", 1000)
HOOK = block("2 MILLIONS", "DE STREAMS", 980, 520)
LOGO_S = rgba_file(os.path.join(REPO, "showreel/assets/logos/monsieur-vass.png"), 200)

def player(img, t, k):
    """The clip inside a rounded, glowing frame with a red progress bar, entering with a 3D tilt."""
    w, h = 620, 651; f = cv2.resize(clip(t), (w, h), interpolation=cv2.INTER_AREA)
    rgba = np.dstack([f[..., ::-1], np.ones((h, w), np.float32)])
    m = np.zeros((h, w), np.uint8); cv2.rectangle(m, (24, 0), (w - 25, h - 1), 255, -1); cv2.rectangle(m, (0, 24), (w - 1, h - 25), 255, -1)
    for cx, cy in ((24, 24), (w - 25, 24), (24, h - 25), (w - 25, h - 25)): cv2.circle(m, (cx, cy), 24, 255, -1, cv2.LINE_AA)
    rgba[..., 3] = m / 255
    p = (t + T0) / 42.8; rgba[h - 12:h - 4, 20:20 + int((w - 40) * p), :3] = (1.0, 0.16, 0.16)       # progress bar
    rgba = glow_rgba(rgba, (255, 50, 60), 20, 0.9)
    hh, ww = rgba.shape[:2]; tilt = 0.06 + (1 - ease(k / 0.6)) * 0.18
    src = np.float32([[0, 0], [ww, 0], [ww, hh], [0, hh]]); dy = tilt * hh
    rgba = cv2.warpPerspective(rgba, cv2.getPerspectiveTransform(src, np.float32([[0, dy], [ww, 0], [ww, hh], [0, hh - dy]])), (ww, hh))
    cv.paste(img, rgba, W / 2, 520, (0.8 + 0.2 * ease(k / 0.4)) * popk(k), min(k / 0.12, 1))

burn = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LIB, "transitions/burn-transition-12.mp4"), "-vf",
                       f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                      capture_output=True, check=True).stdout
BURN = np.frombuffer(burn, np.uint8).reshape(-1, H, W, 3); BP = 11 / 30
CUTS = [T_PROOF, T_BACK]
COUNT_T, COUNT_D = T_PROOF + 0.6, 3.0                 # card appears at T_PROOF+0.6, counter runs after +0.45 s

VIDEO_ONLY = f"{WORK}/video_only.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-vf", "noise=alls=3:allf=t+u,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "19", VIDEO_ONLY], stdin=subprocess.PIPE)
for n in range(int(END * FPS)):
    t = n / FPS
    if t < T_PROOF:
        img = full(t); k = t
        if k >= 0.1: cv.paste(img, HOOK, W / 2, 330, 0.55 + 0.55 * min((k - 0.1) / 0.12, 1) - 0.1 * min(max(k - 0.22, 0) / 0.1, 1))
    elif t < T_BACK:
        img = cv.bg(t); k = t - T_PROOF
        player(img, t, k)
        draw_stream_card(cv, img, CARD, CARD[1], t, COUNT_T, COUNT_D, 0, 2_000_000, "", W / 2, 1230)
        tk = t - (COUNT_T + 0.45 + COUNT_D)
        if tk > 0:
            im, _ = neon("2 MILLIONS SUR SPOTIFY", 92, RED); cv.paste(img, im, W / 2, 1560, popk(tk), min(tk / 0.08, 1))
        img *= cv.vig * 0.4 + 0.6
    else:
        img = full(t); k = t - T_BACK
        im, _ = neon("2 000 000 DE STREAMS", 104, GOLD); cv.paste(img, im, W / 2, 1520, popk(k - 0.3), min(max(k - 0.3, 0) / 0.08, 1))
        if t > END - 0.4: img *= max(0.0, (END - t) / 0.4)
    for b in CUTS:
        kb = int(round((t - (b - BP)) * FPS))
        if 0 <= kb < len(BURN): img = 1 - (1 - img) * (1 - BURN[kb].astype(np.float32) / 255)
    cv.paste(img, LOGO_S, 130, 130)                                   # his logo, top left, always
    enc.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()

# ---------- sound: the clip's music as recorded + SFX ----------
def load(p, ss=0.0, d=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss)] + (["-t", str(d)] if d else []) + ["-i", p, "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.check_output(cmd), np.float32).reshape(-1, 2).copy()
L = int(END * SR); mix = np.zeros((L, 2), np.float32)
def place(snd, t, g):
    i0 = max(int(t * SR), 0); n = min(len(snd), L - i0)
    if n > 0: mix[i0:i0 + n] += snd[:n] * g
music = load(REC, T0, END)[:L]; env = np.ones(len(music), np.float32)
i0, i1 = int(COUNT_T * SR), int((COUNT_T + 0.45 + COUNT_D + 0.6) * SR); r = int(0.2 * SR)
env[i0:i1] = 0.6; env[i0 - r:i0] = np.linspace(1, 0.6, r); env[i1:i1 + r] = np.linspace(0.6, 1, r)      # light duck under the counter
env[-int(0.4 * SR):] *= np.linspace(1, 0, int(0.4 * SR)); place(music * env[:, None], 0, 1.0)
S = lambda f: os.path.join(LIB, "sfx", f)
place(load(S("synth-hit.wav")), 0.1, 0.5)
burn_a = load(os.path.join(LIB, "transitions/burn-transition-12.mp4"))
for b in CUTS: place(burn_a, b - BP, 0.4)
place(load(S("whoosh-2.mp3")), T_PROOF - 0.15, 0.3); place(load(S("whoosh-3.mp3")), T_BACK - 0.15, 0.3)
place(load(S("camera-shutter-short.mp3")), T_PROOF + 0.05, 0.5)
mc = load(S("money-counter.mp3"), 0.6, COUNT_D); mc[-int(0.1 * SR):] *= np.linspace(1, 0, int(0.1 * SR))[:, None]
place(mc, COUNT_T + 0.45, 0.5); place(load(S("cash-ding.mp3")), COUNT_T + 0.45 + COUNT_D - 0.1, 0.55)
place(load(S("synth-hit.wav")), T_BACK + 0.3, 0.45)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO_ONLY, "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", "alimiter=limit=0.89:level=false", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000",
                "-movflags", "+faststart", "-shortest", OUT], input=mix.tobytes(), check=True)
print("done", OUT, f"{END:.1f}s")
