#!/usr/bin/env bash
# Method 3 (videos built from code): installs the plugins and skills into a fresh container.
# Usage: bash tools/code-video/setup.sh
set -u
cd "$(dirname "$0")"

claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes
claude plugin marketplace add pbakaus/impeccable
claude plugin install impeccable@impeccable
claude plugin marketplace add anthropics/claude-plugins-official
claude plugin install frontend-design@claude-plugins-official

npx -y skills add remotion-dev/skills --all -g -y
npx -y skills add https://github.com/Leonxlnx/taste-skill --all -g -y
npx -y skills@latest add emilkowalski/skills --all -g -y

# video-use (cuts pauses/fillers by transcript). Transcription goes to ElevenLabs Scribe and
# spends the account's credits; the proxy injects the key, the placeholder only satisfies the script.
if [ ! -d "$HOME/video-use" ]; then
  git clone -q --depth 1 https://github.com/browser-use/video-use "$HOME/video-use"
  ln -sfn "$HOME/video-use" "$HOME/.claude/skills/video-use"
  echo "ELEVENLABS_API_KEY=injected-by-proxy" > "$HOME/video-use/.env"
fi

# cdn.jsdelivr.net is blocked by the proxy: GSAP is shipped locally in template/assets
if [ ! -f template/assets/gsap.min.js ]; then
  tmp=$(mktemp -d); (cd "$tmp" && npm i gsap@3.14.2 --silent) && cp "$tmp/node_modules/gsap/dist/gsap.min.js" template/assets/
fi
echo "Restart the session (or rely on the live skill reload) so the new skills are listed."
