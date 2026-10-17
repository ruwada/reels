# Reel 20 v2: CRM becomes a database (effects + HyperFrames re-edit)

Sources: Drive original «20 рилс.mp4» (4K, 45 s), stock clips of broll.json. Outputs stay outside git.

    python3 cut.py ORIG.mp4 WORK                  # pauses trimmed, jump-cut zooms -> WORK/base.mp4, voice.wav, timeline.json
    python3 fxsegs.py ORIG.mp4 WORK               # tools/fx effects spliced in -> WORK/base_fx.mp4
    ffmpeg -i WORK/base_fx.mp4 -vf tpad=stop_mode=clone:stop_duration=1.6 ... HF/assets/base.mp4   # CTA hold
    python3 prep_broll.py CAND HF/assets/broll    # 5 clips cut to their slots
    python3 build.py HF 1.6                       # HyperFrames page: CRM routine scene, question punch, agent/human split, CTA, subtitles
    npx hyperframes@0.8.121 render -o render.mp4 --fps 30
    python3 mix.py render.mp4 voice_pad.wav master.mp4   # + 2 quiet whooshes, loudnorm -14
    x265 2-pass 7 Mbit/s for the Telegram bot (< 50 MB)

Effects (tools/fx): 17 glass type «CRM» behind the head (hook), 05 digital zoom on «AI-агенты» (4K crop),
07 checklist of the agent's 7 steps, 08 headline wall «какую CRM купить?».
Look: warm graphite + orange #FF7A2F, cream subtitle chip with ink text (not the blue of 19, not the cyan of 20 v1).
Gotcha: the last segment of cut.py runs past the end of the source; timeline.json duration was set to the real frame count (1331).
