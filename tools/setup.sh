#!/bin/bash
# Installs the video toolkit: HyperFrames (+ Parakeet transcription), Whisper, and the Python libs used by scripts/.
# Safe to re-run: every step is skipped when already done.
# Models come from GitHub releases of k2-fsa/sherpa-onnx (Hugging Face is not reachable from the cloud sandbox).
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
REL=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
mkdir -p ~/models ~/.local/bin

# --- Python libs (transcription, face tracking, image work)
[ -x ~/.venvs/media/bin/python ] || python3 -m venv ~/.venvs/media
~/.venvs/media/bin/pip install -q sherpa-onnx soundfile numpy scipy "opencv-python-headless<5" pillow fonttools brotli

# --- Parakeet (word-level timestamps, used by HyperFrames and scripts/)
P=sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8
[ -f ~/models/$P/encoder.int8.onnx ] || curl -sSL "$REL/$P.tar.bz2" | tar xj -C ~/models

# --- Whisper small (OpenAI Whisper, ONNX export)
W=sherpa-onnx-whisper-small
[ -f ~/models/$W/small-encoder.onnx ] || curl -sSL "$REL/$W.tar.bz2" | tar xj -C ~/models
cp "$REPO/tools/whisper.py" ~/.local/bin/whisper.py
printf '#!/bin/sh\nexec "$HOME/.venvs/media/bin/python" -I "$HOME/.local/bin/whisper.py" "$@"\n' > ~/.local/bin/whisper
chmod +x ~/.local/bin/whisper
ln -sf ~/.local/bin/whisper /usr/local/bin/whisper 2>/dev/null || true

# --- HyperFrames
command -v hyperframes >/dev/null || npm install -g hyperframes
hyperframes telemetry disable >/dev/null 2>&1 || true
hyperframes browser ensure >/dev/null
D=~/.cache/hyperframes/parakeet/parakeet-tdt-0.6b-v3-int8
mkdir -p "$D"
for f in encoder.int8.onnx decoder.int8.onnx joiner.int8.onnx tokens.txt; do
  [ -e "$D/$f" ] || ln -s ~/models/$P/$f "$D/$f"
done
hyperframes models install parakeet >/dev/null
# HyperFrames agent skills (installed by init into ~/.claude/skills)
[ -d ~/.claude/skills/hyperframes ] || (cd /tmp && rm -rf _hf_skills && hyperframes init _hf_skills --non-interactive >/dev/null && rm -rf _hf_skills)
# GSAP vendored locally: cdn.jsdelivr.net is not reachable from the sandbox, so compositions load ./gsap.min.js
V=~/.cache/hyperframes/vendor
if [ ! -f $V/gsap.min.js ]; then
  mkdir -p $V && (cd $V && npm pack gsap@3.15.0 --silent >/dev/null && tar xzf gsap-3.15.0.tgz && cp package/dist/gsap.min.js . && rm -rf package gsap-3.15.0.tgz)
fi
# --- YouTube MCP server (ia-programming/youtube-mcp), pinned to the audited commit.
# eval() on search results is replaced by ast.literal_eval() (data only, never executes code).
# Needs GOOGLE_API_KEY in the environment, and youtube.com allowed by the network policy.
Y=~/mcp/youtube-mcp
if [ ! -f $Y/.venv/bin/python ]; then
  rm -rf $Y && mkdir -p $Y && cd $Y && git init -q && git remote add origin https://github.com/ia-programming/youtube-mcp
  git fetch -q --depth 1 origin d881b90116700e5e00069a7a74aaf7c0d18693a1 && git checkout -q FETCH_HEAD
  sed -i 's/^import os, sys$/import os, sys, ast/; s/parsed_results = eval(results)/parsed_results = ast.literal_eval(results)/' server.py
  # McpError takes an ErrorData in current mcp versions; the original call hid every real error
  sed -i 's/^from mcp.types import Tool, TextContent, ListToolsResult, INVALID_PARAMS$/from mcp.types import Tool, TextContent, ListToolsResult, INVALID_PARAMS, ErrorData/; s/raise McpError(INVALID_PARAMS, str(e))/raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))/' server.py
  grep -q "ast.literal_eval(results)" server.py || { echo "youtube-mcp patch failed" >&2; exit 1; }
  grep -q "McpError(ErrorData" server.py || { echo "youtube-mcp patch failed" >&2; exit 1; }
  uv sync --frozen -q
  cd - >/dev/null
fi
# --- Caption fonts (Fontsource on npm -> TTF for libass/PIL): Montserrat Black, Luckiest Guy, Anton,
# Bebas Neue, Poppins Black, Archivo Black
mkdir -p ~/.fonts
if [ ! -f ~/.fonts/anton-latin-400.ttf ]; then
  T=$(mktemp -d)
  for f in montserrat:900 luckiest-guy:400 anton:400 bebas-neue:400 poppins:900 archivo-black:400; do
    n=${f%%:*}; w=${f##*:}
    (cd "$T" && npm pack --silent "@fontsource/$n" >/dev/null && tar xzf fontsource-$n-*.tgz && \
      ~/.venvs/media/bin/python -I -c "from fontTools.ttLib import TTFont; f=TTFont('package/files/$n-latin-$w-normal.woff2'); f.flavor=None; f.save('$HOME/.fonts/$n-latin-$w.ttf')" && rm -rf package fontsource-$n-*.tgz)
  done
  rm -rf "$T"; fc-cache -f >/dev/null
fi

# --- Remotion project dependencies
[ -d "$REPO/remotion/node_modules" ] || (cd "$REPO/remotion" && npm ci --silent)
echo "Video toolkit ready: hyperframes, whisper, parakeet, youtube-mcp, remotion"
