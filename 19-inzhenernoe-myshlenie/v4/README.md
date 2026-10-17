# Reel 19 v4: engineering thinking, re-edited with tools/fx effects (style of reels 20 v2 and 21)

Sources: Drive original (id 1QpoAEP5nUqjbU_5EUdA7Q5fd3-PLZOAr, 4K, 68.6 s), ../words.json, stock clips of broll.json.
Outputs stay outside git.

    python3 cut.py ORIG.mov WORK                  # pauses trimmed, jump-cut zooms -> WORK/base.mp4, voice.wav, timeline.json
    bash ../../tools/fx/setup.sh                  # once per container
    python3 fx19.py ORIG.mov WORK                 # 8 effects rendered and spliced -> WORK/base_fx.mp4, fxspans.json
    cp WORK/base_fx.mp4 HF/assets/base.mp4
    python3 prep_broll.py CAND HF/assets/broll    # 5 clips cut to their slots
    python3 build.py ru HF                        # HyperFrames page: «наоборот», PR queue, foundation, punch, CTA, subtitles
    PUPPETEER_EXECUTABLE_PATH=/opt/pw-browsers/chromium npx hyperframes@0.8.121 render -o render.mp4 --fps 30
    python3 mix.py render.mp4 WORK/voice.wav master.mp4   # + 2 quiet whooshes on the scene entries, loudnorm -14

Effects: 16 cover story «СЕНЬОРЫ» (hook) · 17 glass «ЧЕЛОВЕК» · 05 digital zoom on «быстрее» · 07 checklist
«AI умеет» with a red «подходит ЭТОМУ проекту?» · 08 headline wall of the four questions (he keeps his size) ·
01 orbit of AI tool chips · 15 vertigo on «куда направлять» · 06 phone with the Telegram post, guide №11.
Look: ink + lime #C8F25A, the spoken word turns ink on a tilted lime chip (not the orange of 20, not the pink of 21).

Fixes against v3: cut.py spans are contiguous (v3 overlapped by 0.1 s at joins = the stutter) and the last span
stops at the end of the source; fx19.py seeks with 4 decimals and a quarter-frame lead, because the 3-decimal
seek of fxlib.Clip put the zoom and vertigo one frame early and the checklist one frame late (lips off by a frame,
a trimmed frame flashing at the join); mattes are computed shot by shot so smoothing never ghosts across a cut.
