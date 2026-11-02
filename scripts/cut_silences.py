"""Rotate (optional), remove the silences of a face-cam clip and export subtitles for him to correct.
Silences: 20 ms frames below median - 10 dB for >= 0.16 s are cut, 0.05 s kept on each side; the last
`--keep-tail` seconds are kept whole (his sign-off is spoken softly). Segments are extracted frame-exact and
joined with the concat demuxer (no lip-sync drift). Audio: loudness -14 LUFS, true peak <= -1.5 dBFS.
Subtitles: SRT on the cut timeline, short lines (<= 7 words or 2.6 s), plus a numbered .txt for corrections.
usage: cut_silences.py SRC WORDS.json OUT.mp4 OUT.srt [--transpose] [--keep-tail 6] [--fixes fixes.json]
fixes.json: [[time_s, "new word"], ...] replaces the word nearest to time_s ("" deletes it)."""
import sys, os, json, subprocess, argparse, numpy as np, soundfile as sf

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("words"); ap.add_argument("out"); ap.add_argument("srt")
ap.add_argument("--transpose", action="store_true"); ap.add_argument("--keep-tail", type=float, default=6.0)
ap.add_argument("--fixes")
a = ap.parse_args()
FPS = 30
work = os.path.splitext(a.out)[0] + "_work"; os.makedirs(work, exist_ok=True)

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-ac", "1", "-ar", "16000", f"{work}/a.wav"], check=True)
au, sr = sf.read(f"{work}/a.wav"); END = len(au) / sr; hop = int(0.02 * sr)
db = 20 * np.log10(np.array([np.sqrt(np.mean(au[i:i + hop] ** 2)) for i in range(0, len(au) - hop, hop)]) + 1e-9)
db = np.convolve(db, np.ones(3) / 3, mode="same")
keep = db >= np.median(db) - 10
i = 0
while i < len(keep):
    if not keep[i]:
        j = i
        while j < len(keep) and not keep[j]: j += 1
        if (j - i) * 0.02 < 0.16: keep[i:j] = True
        else: keep[i:i + 3] = True; keep[max(j - 3, i):j] = True
        i = j
    else: i += 1
keep[int(max(0, END - a.keep_tail) / 0.02):] = True
runs = []
for k, v in enumerate(keep):
    if v:
        if runs and runs[-1][1] == k: runs[-1][1] = k + 1
        else: runs.append([k, k + 1])
segs = [[r0 * 0.02, r1 * 0.02] for r0, r1 in runs if (r1 - r0) * 0.02 >= 0.12]
segs[-1][1] = END

# frame-exact segments, then concat
vf = ("transpose=1," if a.transpose else "") + "scale=1080:1920,fps=30"
lst = []
for n, (s0, s1) in enumerate(segs):
    nf = max(1, round((s1 - s0) * FPS)); d = nf / FPS; p = f"{work}/s{n:03d}.mov"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s0:.3f}", "-i", a.src, "-frames:v", str(nf), "-t", f"{d:.4f}", "-vf", vf,
                    "-af", f"afade=t=in:d=0.01,afade=t=out:st={max(d - 0.012, 0):.3f}:d=0.012,apad,atrim=0:{d:.4f}",
                    "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", p], check=True)
    lst.append(f"file '{p}'")
    segs[n][1] = s0 + d
open(f"{work}/list.txt", "w").write("\n".join(lst) + "\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c", "copy", f"{work}/cut.mov"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{work}/cut.mov", "-af",
                "highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000,alimiter=limit=0.7:level=false,aformat=sample_fmts=s16:channel_layouts=stereo",
                "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-cutoff", "18000",
                "-movflags", "+faststart", a.out], check=True)
DUR = sum(s1 - s0 for s0, s1 in segs)
def remap(t):
    acc = 0.0
    for s0, s1 in segs:
        if t < s0: return acc
        if t < s1: return acc + t - s0
        acc += s1 - s0
    return acc

# words -> subtitle lines on the cut timeline
words = sorted(json.load(open(a.words)), key=lambda w: w["s"])
if a.fixes:
    for t, txt in json.load(open(a.fixes)):
        x = min(words, key=lambda w: abs(w["s"] - t))
        if txt: x["w"] = txt
        else: words.remove(x)
merged = []
for w in words:                                   # glue stray punctuation tokens to the previous word
    if merged and w["w"].strip() in {",", ".", "?", "!", "…"}: merged[-1]["w"] += w["w"].strip(); continue
    merged.append(dict(w))
for k, w in enumerate(merged):
    nxt = merged[k + 1]["s"] if k + 1 < len(merged) else END
    w["e"] = min(nxt, w["s"] + 0.12 + 0.065 * len(w["w"]))
lines, cur = [], []
for w in merged:
    cur.append(w)
    end = w["w"][-1]
    if (end in ".?!…" and len(cur) >= 2) or (end == "," and len(cur) >= 4) or len(cur) >= 7 or cur[-1]["e"] - cur[0]["s"] > 2.6:
        lines.append(cur); cur = []
if cur: lines.append(cur)
def ts(t):
    ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
srt, txt = [], []
for n, l in enumerate(lines, 1):
    s0, s1 = remap(l[0]["s"]), max(remap(l[-1]["e"]), remap(l[0]["s"]) + 0.4)
    text = " ".join(w["w"] for w in l)
    srt.append(f"{n}\n{ts(s0)} --> {ts(s1)}\n{text}\n")
    txt.append(f"{n:>2}. [{ts(s0)[3:8]}] {text}")
open(a.srt, "w").write("\n".join(srt))
open(os.path.splitext(a.srt)[0] + ".txt", "w").write("\n".join(txt) + "\n")
print(f"{len(segs)} segments, {DUR:.1f}s (from {END:.1f}s), {len(lines)} subtitle lines")
