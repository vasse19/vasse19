"""Synthesizes the 15 s showreel bed: 128 BPM electro-house in A minor.
Structure (beats): 0-3 filtered intro + build, 4 DROP 1, 4-19 groove, 20-23 break with snare roll,
24 DROP 2, 24-29 groove, 30 final stab ringing out to 15.0 s."""
import sys, numpy as np
from scipy.signal import butter, sosfilt, lfilter
import soundfile as sf

SR, BPM, DUR = 48000, 128, 15.0
B = 60 / BPM                      # one beat = 0.46875 s; 32 beats = 15.0 s
N = int(SR * DUR)
rng = np.random.default_rng(128)
t = np.arange(N) / SR
mix = np.zeros((N, 2))

def at(beat): return int(round(beat * B * SR))
def add(sig, beat, gain=1.0, pan=0.0):
    i = at(beat); sig = sig[:max(0, N - i)]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    mix[i:i + len(sig), 0] += sig * gain * l * 1.414
    mix[i:i + len(sig), 1] += sig * gain * r * 1.414
def env(n, a=0.002, d=0.2):
    x = np.arange(n) / SR
    return np.minimum(x / a, 1) * np.exp(-x / d)
def lp(x, f, o=2): return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)
def saw(freq, n, detune=0.0):
    ph = np.cumsum(np.full(n, freq * (1 + detune)) / SR) + rng.random()
    return 2 * (ph % 1) - 1
NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)

# ---- drums
def kick():
    n = int(0.42 * SR); x = np.arange(n) / SR
    f = 45 + 110 * np.exp(-x / 0.035)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.22)
    click = hp(rng.standard_normal(n), 2500) * np.exp(-x / 0.004) * 0.35
    return np.tanh((body + click) * 1.6)
def clap():
    n = int(0.3 * SR); x = np.arange(n) / SR; nz = bp(rng.standard_normal(n), 900, 3500)
    e = sum(np.exp(-np.maximum(x - o, 0) / 0.008) * (x >= o) for o in (0, 0.011, 0.022)) * 0.6 + np.exp(-x / 0.09) * (x >= 0.022)
    return nz * e * 0.9
def snare(level=1.0):
    n = int(0.18 * SR); x = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 190 * x) * np.exp(-x / 0.05) * 0.5
    return (bp(rng.standard_normal(n), 1200, 7000) * np.exp(-x / 0.06) + tone) * level
def hat(open_=False):
    n = int((0.22 if open_ else 0.045) * SR); x = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7500) * np.exp(-x / (0.07 if open_ else 0.012))

K, CL = kick(), clap()
groove = [b for b in range(4, 30) if not 20 <= b < 24]
for b in groove:
    add(K, b, 0.95)
    if b % 2 == 1: add(CL, b, 0.55, 0.05)
    add(hat(True), b + 0.5, 0.16, 0.25)
    for s in (0.25, 0.75): add(hat(), b + s, 0.09, -0.3)
# intro: muffled four-on-floor teaser on beats 2-3
for b in (2, 3): add(lp(K, 300), b, 0.5)
# snare roll building into drop 1 (beat 3) and drop 2 (beats 20-23)
for i in range(8): add(snare(0.25 + 0.06 * i), 3 + i / 8, 0.5)
roll = [20 + i / 2 for i in range(4)] + [22 + i / 4 for i in range(4)] + [23 + i / 8 for i in range(8)]
for i, b in enumerate(roll): add(snare(0.35 + 0.65 * i / len(roll)), b, 0.55, 0.1 * ((-1) ** i))

# ---- sidechain pump (ducks everything melodic on each kick)
duck = np.ones(N)
for b in groove:
    i = at(b); n = min(int(0.35 * SR), N - i); x = np.arange(n) / SR
    duck[i:i + n] = np.minimum(duck[i:i + n], 1 - 0.75 * np.exp(-x / 0.09))

# ---- harmony: Am | F | C | G per bar (bar = 4 beats)
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]]
ROOTS = [45, 41, 48, 43]
music = np.zeros(N)
bassline = np.zeros(N)
for bar in range(8):
    ch, root = CHORDS[bar % 4], ROOTS[bar % 4]
    i0, i1 = at(bar * 4), at(bar * 4 + 4)
    n = i1 - i0
    pad = sum(saw(NOTE(m + 12), n, d) for m in ch for d in (-0.008, 0, 0.007)) / 9
    cutoff = 900 if bar == 0 else (1600 if bar in (5,) else 3200)
    if bar == 0:  # intro filter sweep opening into the drop
        pad = np.concatenate([lp(pad[k:k + n // 8], 300 + 2400 * k / n) for k in range(0, n, n // 8)])[:n]
    else:
        pad = lp(pad, cutoff)
    music[i0:i1] += pad * (0.55 if bar else 0.45)
    if bar >= 1 and not (bar == 5):          # offbeat bass, silent during the break
        for q in range(8):
            j = at(bar * 4 + q / 2 + 0.25); m = int(0.2 * SR)
            if j + m > N: continue
            note = saw(NOTE(root - 12), m) * env(m, 0.003, 0.12)
            bassline[j:j + m] += lp(note, 700) * 0.9
    if bar >= 1:                              # 16th pluck arpeggio, the hook
        arp = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 24]
        for s in range(16):
            if bar == 5 and s % 2: continue
            j = at(bar * 4 + s / 4); m = int(0.16 * SR)
            if j + m > N: continue
            p = (saw(NOTE(arp[s % 4]), m) + 0.6 * np.sin(2 * np.pi * NOTE(arp[s % 4]) * np.arange(m) / SR)) * env(m, 0.002, 0.05)
            music[j:j + m] += lp(p, 5000) * (0.22 if bar != 5 else 0.14)
music = music * duck; bassline = bassline * duck

# final stab on beat 30: full Am chord, long ring with echoes
i = at(30); n = N - i
stab = sum(saw(NOTE(m + 12), n, d) for m in [57, 60, 64, 69] for d in (-0.01, 0, 0.009)) / 12
stab = lp(stab, 2600) * env(n, 0.003, 0.5)
stab += np.sin(2 * np.pi * NOTE(33) * np.arange(n) / SR) * env(n, 0.003, 0.6) * 0.8
music[i:] += stab * 0.9
add(K, 30, 1.0)

# ---- noise riser into drop 2 (beats 20-24) and into drop 1 (beats 1-4)
def riser(b0, b1, gain):
    i0, i1 = at(b0), at(b1); n = i1 - i0
    nz = rng.standard_normal(n); out = np.zeros(n); seg = n // 16
    for k in range(16):
        out[k * seg:(k + 1) * seg] = bp(nz[k * seg:(k + 1) * seg], 400 + 7000 * k / 16, 1200 + 9000 * k / 16)
    return out * np.linspace(0, 1, n) ** 2 * gain, b0
for r in (riser(1, 4, 0.35), riser(20, 24, 0.45)): add(*r)

# ---- stereo + simple reverb (two delayed, filtered taps)
mel = np.stack([music, music], 1)
for d, g, side in ((0.0113, 0.0, 0), (B * 0.75, 0.22, 0), (B * 0.5, 0.18, 1)):
    if g == 0: continue
    k = int(d * SR); tap = lp(np.concatenate([np.zeros(k), music[:-k]]), 3000) * g
    mel[:, side] += tap
mix += mel * 0.8
mix[:, 0] += bassline * 0.8; mix[:, 1] += bassline * 0.8

# master: gentle glue, soft clip, fade the very end
mix = np.tanh(mix * 0.9) * 0.9
mix[-int(0.25 * SR):] *= np.linspace(1, 0, int(0.25 * SR))[:, None]
sf.write(sys.argv[1], mix.astype(np.float32), SR)
print("wrote", sys.argv[1])
