"""Fake multi-camera podcast edit (Club Shay Shay style) from one wide shot:
virtual cameras (wide, close-up host, close-up guest, extreme close-up), cut on the active speaker,
listener reaction shots, slow push-ins, warm cinematic grade."""
import sys, subprocess, json, numpy as np, cv2

SRC, OUT = sys.argv[1:3]
FACES = json.loads(sys.argv[3])          # {"host": [x, y], "guest": [x, y]} face centres in source pixels
W, H, FPS = 1920, 1080, 30
probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                            "stream=width,height:format=duration", "-of", "json", SRC]))
SW, SH = probe["streams"][0]["width"], probe["streams"][0]["height"]
DUR = float(probe["format"]["duration"]); N = int(DUR * FPS); ft = np.arange(N) / FPS

# ---------- who is speaking: mouth-region motion, smoothed ----------
def mouth_box(name):
    x, y = FACES[name]; r = SH * 0.09
    return int(x - r), int(x + r), int(y + r * 0.3), int(y + r * 1.6)
boxes = {k: mouth_box(k) for k in FACES}
cap = cv2.VideoCapture(SRC); prev = None; mot = []
while True:
    ok, f = cap.read()
    if not ok: break
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
    if prev is not None:
        d = np.abs(g - prev)
        mot.append([d[y0:y1, x0:x1].mean() for x0, x1, y0, y1 in boxes.values()])
    prev = g
mot = np.array(mot); mot = np.vstack([mot[:1], mot])
k = int(0.6 * FPS); ker = np.ones(k) / k
sm = np.stack([np.convolve(mot[:, j], ker, mode="same") for j in range(mot.shape[1])], 1)
sm = sm / np.median(sm, axis=0)                       # each person relative to their own resting level
names = list(FACES)
speaker = np.array([names[int(np.argmax(r))] for r in sm])[:N]
speaker = np.concatenate([speaker, np.repeat(speaker[-1:], max(0, N - len(speaker)))])

# ---------- shot list ----------
shots = []                                             # (start_frame, camera)
cur, start, last_switch, n_same = None, 0, 0, 0
i = 0
rng = np.random.default_rng(3)
while i < N:
    spk = speaker[i]
    seg_end = i
    while seg_end < N and speaker[seg_end] == spk: seg_end += 1
    if seg_end - i < int(1.4 * FPS) and shots:         # too short: not a real turn, stay on the previous shot
        i = seg_end; continue
    t = i
    other = [n for n in names if n != spk][0]
    shots.append((t, f"cu_{spk}"))
    # long turns: cut away to the wide shot or a listener reaction every 4-7 s
    t += int(rng.uniform(4, 6.5) * FPS)
    alt = 0
    while t < seg_end - int(1.6 * FPS):
        if alt % 3 == 0: shots.append((t, "wide")); t += int(2.2 * FPS)
        elif alt % 3 == 1: shots.append((t, f"cu_{other}")); t += int(1.3 * FPS)
        else: shots.append((t, f"xcu_{spk}")); t += int(2.5 * FPS)
        if t < seg_end - int(1.2 * FPS): shots.append((t, f"cu_{spk}"))
        t += int(rng.uniform(4, 6.5) * FPS); alt += 1
    i = seg_end
shots[0] = (0, "wide")                                 # open on the wide shot
shots.sort()
cam_of = np.empty(N, dtype=object); shot_start = np.zeros(N, int)
for j, (s0, cam) in enumerate(shots):
    e0 = shots[j + 1][0] if j + 1 < len(shots) else N
    cam_of[s0:e0] = cam; shot_start[s0:e0] = s0
print(len(shots), "shots,", sum(1 for s in shots if s[1] == "wide"), "wide", flush=True)

def rect(cam, push):
    """Source crop (x0, y0, w, h) for a virtual camera, with a slow push-in factor."""
    if cam == "wide":
        h = SH / (1.0 + 0.05 * push); cx, cy = SW / 2, SH / 2
    else:
        kind, who = cam.split("_", 1); x, y = FACES[who]
        h = SH * (0.56 if kind == "cu" else 0.40) / (1.0 + 0.07 * push); cx, cy = x, y + h * 0.08
    w = h * W / H
    return np.clip(cx - w / 2, 0, SW - w), np.clip(cy - h / 2, 0, SH - h), w, h

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
VF = ("unsharp=7:7:0.9,eq=contrast=1.1:saturation=1.05:gamma=0.97,colorbalance=rs=0.03:bs=-0.04:rm=0.02:bm=-0.02,"
      "vignette=angle=PI/5,noise=alls=3:allf=t+u,format=yuv420p")
VO = OUT + ".video.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-vf", VF, "-c:v", "libx264", "-preset", "medium", "-crf", "19", VO], stdin=subprocess.PIPE)
FR = SW * SH * 3
for i in range(N):
    buf = dec.stdout.read(FR)
    if len(buf) < FR: break
    fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
    s0 = shot_start[i]; e0 = next((s for s, _ in shots if s > s0), N)
    push = (i - s0) / max(e0 - s0, 1)
    x0, y0, w, h = rect(cam_of[i], push)
    M = np.array([[W / w, 0, -x0 * W / w], [0, H / h, -y0 * H / h]])
    enc.stdin.write(cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT).tobytes())
enc.stdin.close(); enc.wait()
dec.stdout.close(); dec.kill(); dec.wait()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VO, "-i", SRC, "-filter_complex",
                "[1:a]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,loudnorm=I=-14:TP=-2:LRA=8,"
                "aresample=48000,asetpts=N/SR/TB,alimiter=limit=0.75:level=false[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, flush=True)
