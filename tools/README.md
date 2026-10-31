# Video toolkit

`tools/setup.sh` installs everything the editing scripts in `scripts/` need. It is safe to re-run.

| Tool | Command | What it does |
|---|---|---|
| HyperFrames | `hyperframes` | HTML → MP4 video compositions (render, captions, transcribe with Parakeet) |
| Whisper (small) | `whisper FILE --lang fr` | Transcribes audio/video, writes `.txt` and `.srt` |
| Remotion | `cd remotion && npx remotion render <Composition> out/x.mp4` | React video framework (project in `remotion/`, run `npm install` first) |
| Parakeet | used by `hyperframes transcribe` and `scripts/asr.py` | Word-level timestamps (best for animated captions) |

Notes for the cloud sandbox:
- Hugging Face, openaipublic and cdn.jsdelivr.net are blocked; models come from the GitHub releases of `k2-fsa/sherpa-onnx`.
- HyperFrames compositions must load GSAP locally: copy `~/.cache/hyperframes/vendor/gsap.min.js` into the project and use `<script src="gsap.min.js">`.
- Remotion's browser download (remotion.media) is blocked; `remotion/remotion.config.ts` uses the preinstalled Chrome Headless Shell from `/opt/pw-browsers` instead.
- `hyperframes transcribe --engine whisper` needs whisper.cpp ggml models (Hugging Face) and does not work here; use `--engine parakeet` (default when installed) or the `whisper` command.

To run it automatically in every new cloud session, put this line in the environment's setup script:

    bash vasse19/tools/setup.sh
