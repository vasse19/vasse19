"""Build the edit decision list (cold open + jump cuts), render the cut, and remap the transcript."""
import json, sys, subprocess
SRC, WORK = sys.argv[1], sys.argv[2]
words = json.load(open(f"{WORK}/words.json"))
def sub(t0, t1, text):
    global words
    keep = [w for w in words if not (t0 - 0.01 <= w["s"] < t1)]
    new = text.split(); k = len(new)
    words = sorted(keep + [{"w": x, "s": t0 + (t1 - t0) * i / k, "e": t0 + (t1 - t0) * (i + 1) / k} for i, x in enumerate(new)], key=lambda w: w["s"])
words = [w for w in words if w["s"] >= 0.15]
sub(0.15, 1.3, "Quand moi je vous parle en sérieux,")
sub(31.5, 37.4, "YouTube, c'est le Graal. En fait YouTube là, c'est là-bas. Quand je dis c'est là-bas, je dois partir, c'est là-bas.")
sub(40.5, 41.0, "arrêtez,")
words = [w for w in words if w["w"] != "?"]
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else 64.2
    w["e"] = min(nxt, w["s"] + 0.55)

COLD = (43.95, 47.75)                 # "C'est cardio. En fait pour moi YouTube et Twitch c'est deux plateformes qui sont cardio."
DROP = [(13.72, 14.45)]               # repeated "D'accord, je suis d'accord,"
# speech islands from word timings, gaps > 0.3 s squeezed to ~0.1 s
segs = []
for w in words:
    s, e = w["s"] - 0.05, w["e"] + 0.05
    if any(a <= w["s"] < b for a, b in DROP): continue
    if segs and s - segs[-1][1] < 0.12: segs[-1][1] = max(segs[-1][1], e)
    else: segs.append([s, e])
segs = [[max(0, a), b] for a, b in segs]
edl = [list(COLD)] + segs
# map words to the new timeline
out_words, t = [], 0.0
for a, b in edl:
    for w in words:
        if a <= w["s"] < b and not any(x <= w["s"] < y for x, y in DROP):
            out_words.append({"w": w["w"], "s": t + w["s"] - a, "e": t + min(w["e"], b) - a})
    t += b - a
json.dump(out_words, open(f"{WORK}/words_cut.json", "w"), ensure_ascii=False)
json.dump({"edl": edl, "cold_end": COLD[1] - COLD[0], "dur": t}, open(f"{WORK}/edl.json", "w"))
# render the cut (video + audio, tiny fades to avoid clicks)
fc = []
for i, (a, b) in enumerate(edl):
    fc.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{i}]")
fc.append("".join(f"[v{i}][a{i}]" for i in range(len(edl))) + f"concat=n={len(edl)}:v=1:a=1[v][a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-r", "30", "-c:a", "aac", "-b:a", "256k", f"{WORK}/cut.mp4"], check=True)
print(f"{len(edl)} segments, {t:.1f}s (from 64.2s)")
print(" ".join(w["w"] for w in out_words))
