# reels

Reels for [@islam.devai](https://www.instagram.com/islam.devai): the editing tools and the edit plan of
every reel.

Talking-head video in, polished 1080x1920 reel out: word-by-word subtitles (active word in lime),
hook plate, Pexels B-roll, a few motion cards, punch-in zooms, CTA plate, loudness normalised to -14 LUFS.

    tools/                 setup.sh, transcribe.py, render.py, pexels.py, export_project.py
    08-90/, 11-naym/ ...   one folder per reel: edit.json (the plan) and words.json (subtitles)

## Editing a reel

    tools/setup.sh                                          # once per fresh container
    python3 tools/transcribe.py 08-90/orig.mov 08-90/work/  # work/words.json + work/whisper.txt
    # fix spelling in words.json using whisper.txt, save it as 08-90/words.json,
    # write 08-90/edit.json (format in the render.py docstring)
    python3 tools/render.py 08-90/edit.json

Paths in edit.json are relative to its folder. The source video (`orig.*`), stock clips (`broll/`)
and `work/` stay out of git.

B-roll from Pexels (key: API credential for api.pexels.com in the environment, or `PEXELS_API_KEY`):
`python3 tools/pexels.py search "man typing laptop"`, then `python3 tools/pexels.py get <id> 08-90/broll/`.
Check several frames of every clip before using it.

Card kinds: `stat` (animated number), `text`, `list`, `chat` (messenger mock-up, `"frame": "phone"`
draws a Telegram screen in a phone), `clip` (any video file: Pexels stock or the author's own footage).

Card themes (`"theme"` in the plan or per card), pick one per reel to fit its topic and don't repeat
the previous reel's: `dark` (grid on near-black), `paper` (light sheet, marker highlights),
`glass` (frosted panel over the blurred speaker), `terminal` (code window for dev topics).

Transitions (`"transition"`): `smooth` fades, `sharp` slides a card in or hard-cuts a clip with a
quick punch-in. Clips get a mild grade to match the speaker footage (`"grade": false` to skip).

## Handing a reel over to DaVinci Resolve

Optional, only when the author asks for it after seeing the rendered reel: the same plan as an editable
DaVinci Resolve (free) project the author finishes on Windows or Mac.

    python3 tools/export_project.py 08-90/edit.json            # -> 08-90/proekt/

`proekt/` holds `<name>.fcpxml` (V1 speaker split at zooms, V2 B-roll and cards, V3 word-highlight
subtitles as one alpha clip per phrase, V4 hook and CTA), `subtitry.srt`, `KAK-OTKRYT.txt` and `media/`.
The original video is not copied: the author drops it into `media/` under its own name. Zip `proekt/`
and send it. Transitions and the -14 LUFS loudness step are added in Resolve. `proekt/` stays out of git.
