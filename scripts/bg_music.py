"""Background music made from scratch (no samples, so no rights issue): a mellow afro/trap groove, 92 BPM, A minor
(Am - F - C - G), soft kick + rim + shaker hats, warm pad, plucked arpeggio. Meant to sit far under his voice.
usage: bg_music.py OUT.wav SECONDS"""
import sys, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt

OUT, LEN = sys.argv[1], float(sys.argv[2])
SR, BPM = 48000, 92; B = 60 / BPM; BAR = 4 * B
rng = np.random.default_rng(7)
L = int((LEN + 2) * SR); mus = np.zeros(L, np.float32)
tt = lambda d: np.arange(int(d * SR)) / SR
def filt(x, kind, f): return sosfilt(butter(4, f, kind, fs=SR, output="sos"), x).astype(np.float32)
def place(snd, t, g):
    i = int(t * SR); n = min(len(snd), L - i)
    if n > 0: mus[i:i + n] += snd[:n] * g
def kick():
    t = tt(0.4); fr = 52 * (1 + 2.2 * np.exp(-t * 30)); ph = 2 * np.pi * np.cumsum(fr) / SR
    return (np.sin(ph) * np.exp(-t / 0.16)).astype(np.float32)
def rim():
    t = tt(0.12); return filt(rng.normal(0, 1, len(t)).astype(np.float32) * np.exp(-t * 60).astype(np.float32), "bandpass", [1500, 6000]) * 0.5
def shaker(d=0.06):
    t = tt(d); return filt(rng.normal(0, 1, len(t)).astype(np.float32) * np.exp(-t * 55).astype(np.float32), "highpass", 6000) * 0.18
def pad(d, freqs):
    t = tt(d); x = sum(np.sin(2 * np.pi * f * (1 + dt) * t) + 0.3 * np.sin(4 * np.pi * f * (1 + dt) * t) for f in freqs for dt in (-0.003, 0.003))
    env = np.minimum(1, t / 0.8) * np.minimum(1, (d - t) / 0.8)
    return filt((x * env).astype(np.float32), "lowpass", 1400) * 0.05
def pluck(f, d=0.6):
    t = tt(d); return (sum(np.sin(2 * np.pi * f * k * t) / k ** 1.5 * np.exp(-t * (5 + 3 * k)) for k in range(1, 5)) * 0.16).astype(np.float32)
def bass(f, d):
    t = tt(d); return (np.tanh(np.sin(2 * np.pi * f * t) * 1.6) * np.minimum(1, t / 0.02) * np.exp(-t / (d * 0.9)) * 0.35).astype(np.float32)
A, F, C, G = (220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (196.0, 261.63, 329.63), (196.0, 246.94, 293.66)
CH = [A, F, C, G]; ROOT = [55.0, 43.65, 65.41, 49.0]
ARP = [0, 1, 2, 1, 2, 1, 0, 2]
nbar = int(LEN / BAR) + 1
for b in range(nbar):
    t0 = b * BAR; ch = CH[b % 4]
    place(pad(BAR + 0.6, ch), t0, 1.0)
    place(bass(ROOT[b % 4], B * 1.5), t0, 1.0); place(bass(ROOT[b % 4], B), t0 + 2.5 * B, 0.8)
    for k in (0, 2.5): place(kick(), t0 + k * B, 0.55)
    for k in (1, 3): place(rim(), t0 + k * B, 0.35)
    for s in range(8): place(shaker(), t0 + s * B / 2, 0.6 if s % 2 else 0.35)
    if b % 8 >= 2:                                                   # arpeggio comes in after the first 2 bars
        for s, j in enumerate(ARP): place(pluck(ch[j] * 2), t0 + s * B / 2, 0.8)
n = int(LEN * SR); m = mus[:n]
f = int(2.0 * SR); m[:f] *= np.linspace(0, 1, f); m[-f:] *= np.linspace(1, 0, f)
m = m / (np.abs(m).max() + 1e-9) * 0.7
sf.write(OUT, np.stack([m, m], 1), SR)
print("done", OUT, f"{LEN:.1f}s")
