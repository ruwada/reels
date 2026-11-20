# Reel 19 v3: engineering thinking, Russian original + English voice-over

Steps (sources are the Drive original and stock clips; outputs stay outside git):

    python3 cut.py ORIG.mov WORK           # pauses trimmed, jump-cut zooms -> WORK/base.mp4, voice.wav, timeline.json
    python3 prep_broll.py CAND HF/assets/broll   # 8 clips of broll.json cut to their slots
    python3 build.py ru HF                 # HyperFrames page: blueprint scenes, B-roll, subtitles, CTA (guide #11)
    python3 en/tts.py TTS && python3 en/sync.py TTS EN   # English lines in the cloned voice, laid on the Russian sentences
    python3 build.py en HF_EN EN/words-en.json
    npx hyperframes@0.8.121 render -o render.mp4 --fps 30   # in HF / HF_EN (needs assets/base.mp4, fonts, gsap)
    python3 mix.py render.mp4 voice.wav out.mp4            # + 3 quiet whooshes, loudnorm -14

HF/assets: base.mp4, broll/, fonts (Unbounded, Manrope, JetBrains Mono latin+cyrillic), gsap.min.js.
B-roll media must be written into the static HTML (build.py does it): videos added from JS are not rendered.
