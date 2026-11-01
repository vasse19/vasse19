---
name: montage-big-vass
description: House editing style of Monsieur Vass / "le Big Vass" (French music, culture and sport creator). Use for any request to edit, analyse or re-cut one of his videos (Shorts, Reels, TikTok, YouTube long-form), make a thumbnail, a 3D title or an intro, or when he says "comme d'habitude".
---

# Montage « comme d'habitude » — Monsieur Vass

Speak French to him. He films face-cam (car, home studio, hoodie and glasses) and a split-screen
podcast with a guest; topics are rap, music culture, celebrities, sport (he supports Chelsea).
Sign-off: « C'était le Big Vass pour vous servir ».

## Workflow

1. **Analyse first** when asked « analyse la vidéo »: specs, loudness (`hyperframes audio <file> --json`),
   transcript table with timestamps, strengths, weaknesses, what the edit would do. Then wait.
2. **Ask for the images** he wants on mentions (artist photo, covers, logos, clips). Never redraw a logo
   from memory; the sandbox cannot download them (most sites are blocked), so he sends them.
3. **Edit** with `scripts/vlog3.py` (face-cam vertical, the current reference) or `scripts/podcast3.py`
   (split-screen podcast), or `scripts/longform.py` (YouTube 16:9 long-form: hook, his intro kept,
   chapter cards, keyword captions, end screen, chapter list for the description). Copy the script,
   change only the transcript fixes, DROP list, B-roll, cards and keywords. Render into the scratchpad,
   verify, then copy into the repo.
4. **Verify before sending**: contact sheet of key frames, loudness, and a scan for digital-silence
   windows (`< -100 dB`) over the whole file, especially the last 3 s.
5. Commit + push, send the file, then a short French recap with what to check
   (words guessed by ear, passages removed, copyright notes).

## His library (`assets/`)

Transitions, sounds and backgrounds he supplied, kept in the repo (see `assets/README.md`); `vlog3.py` and
`vlog_kali.py` copy them into the work folder automatically. Add every new element he sends there too.

- `assets/transitions/burn-transition-12.mp4`: his « Burn Transition » (peak frame 11, then black)
- `assets/sfx/riser-metallic-transition.mp3`: suspense riser (peak 2.95 s), plus `synth-whoosh/hit/click.wav`
- `assets/backgrounds/red-gradient.mp4`: animated red gradient for neon text screens

## Style parameters

| Element | Setting |
|---|---|
| Output | 1080×1920, 30 fps, H.264 CRF 19, AAC 192k (YouTube long-form: 1920×1080) |
| Hook | 3D title card on frame 1 (`kind: "hook"`), over the artist photo or the strongest line |
| Jump cuts | silences from audio energy: frames below median − 10 dB for ≥ 0.16 s are cut, 0.05 s kept each side; also drop repeats, stutters, filler. Keep the sign-off whole (it is spoken softly) |
| Reframing | shot change every ~2–3 s (Shorts) or 5–8 s (long-form), cycle MED / TIGHT / WIDE, face-tracked; punch-in on emphasis words and on each cut |
| Captions | one word at a time, uppercase, Inter ExtraBold 104 px (font choice pending: Montserrat Black or Anton proposed), yellow `&H0000E5FF`, 8 px black outline + shadow, pop 72 % → 108 % → 100 %, y ≈ 1420 (1600–1620 over B-roll) |
| Emphasis | names / brands in white `&H00FFFFFF`, strong words in red `&H002A2AFF` with a small zoom |
| 3D cards | `scripts/fx3d.py` `text3d`: top line chrome, following lines red, InterDisplay Black Italic, rotated 5°, red blurred backdrop (`card`), over footage (`over`), or end card |
| End card | « LE BIG / VASS » + `showreel/assets/logos/monsieur-vass.png`, replacing any CapCut outro |
| B-roll | photo/cover as a card with gold rim over its own blurred copy; footage: 16:9 centred over blurred copy, or cropped vertical on the subject; muted |
| Transitions | his « Burn Transition » clip, screen-blended, peak (0.39 s in) on 4–5 key moments, its own whoosh |
| SFX | synthesized whoosh on cuts and B-roll, low hit on cards |
| Grade | unsharp 0.5, contrast 1.06, saturation 1.08, light vignette, fine grain |
| Audio | gain to taste (+11 to +18 dB for quiet phone audio), compressor 4:1 at −22 dB, `loudnorm I=-14`, then **`aresample=48000,asetpts=N/SR/TB` before `amix`** (else the voice drops out at the end), limiter 0.75 → about −14 LUFS, peak ≤ −2 dB |

## « Style Kali Muscle » variant (`scripts/vlog_kali.py`)

When he asks for « la même » as the Kali Muscle shorts: motion-design intro over his voice on his red gradient
clip (`Copy_of_Red.mp4`) + drifting grid + embers; neon text in Anton (light core, coloured glow): lines that
stack and pop, typewriter with a white cursor and key clicks; cut-out artist (GrabCut + hole fill, white glow);
covers with glowing rim; counter for numbers (« 6 MILLIONS »); flags drawn in code; face-cam punch-ins every
~2 s, overlays on the dimmed face instead of captions, tunnel vignette on the strongest line; his
`Burn_Transition_12.mp4` (peak frame 11, then black) and `SFX - Riser Metallic Transition.mp3` (peak 2.95 s)
before big reveals; neon yellow Anton 172 captions elsewhere; 3D cards and the end card as usual.

## Thumbnails and titles

`scripts/thumb3d.py` style (like his « MOTEUR COUPÉ » reference): two words, one chrome one glossy red,
3D extrusion, red brush stroke, red mood light, gentle skin smoothing (bilateral at source resolution,
no heavy sharpening). 3D gold intro: `remotion/` composition `GoldIntro` (Remotion + Three.js).

## Constraints to remember

- Uploads are capped at 30 MB: ask for 1080p at ~3.5 Mb/s, 1-minute pieces for long videos, or a
  low-res preview first and then 1080p cuts of the chosen moments.
- No network for youtube.com, capcut.com, Hugging Face, jsDelivr; Google Fonts and npm/PyPI/GitHub work.
- Transcription: Parakeet (word timings, `scripts/asr.py`, `asr_words_win.py` on short windows) and
  Whisper (`whisper FILE --lang fr`) to cross-check. Never invent captions for unclear passages: cut or ask.
- Background renders: never `pkill -f` a pattern that appears in your own command line; when piping
  frames, close and kill the decoder after the loop.
- Mention copyright risk once when he supplies press photos, logos or trailers.
- Long sources (> 2 min): extract each kept segment to its own file with an exact frame count
  (`-frames:v N -t N/30`, audio padded/trimmed to the same length), then the concat demuxer. One filter
  graph with dozens of `trim`s is killed for memory, and `-t` alone adds a frame here and there, which
  drifted lip sync by 0.8 s over 86 segments. Always compare the cut file's video and audio durations.
- Long-form captions: he prefers **keywords only** (pertinent words, names: « BALOO », « INCROYABLE »),
  not full subtitles; keep his own intro as is.
