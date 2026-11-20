#!/usr/bin/env python3
"""Fetch ready text (quran.com), cross-check (alquran.cloud), audio + ayah timing (mp3quran.net).
    python3 fetch.py <name> <read_id> <surah> <from> <to>
Nothing here is typed by hand: every string comes from the APIs and must match across both sources."""
import json, sys, subprocess, urllib.request, os
name, rid, s, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "q"})))
norm = lambda t: ''.join(c for c in t if c not in '\u0640\u06ed\u06e2\ufeff').strip()
reads = {x['id']: x for x in get("https://www.mp3quran.net/api/v3/ayat_timing/reads")}
tim = {x['ayah']: x for x in get(f"https://www.mp3quran.net/api/v3/ayat_timing?surah={s}&read={rid}")}
ayat = []
for v in range(a, b + 1):
    q = get(f"https://api.quran.com/api/v4/verses/by_key/{s}:{v}?translations=45&words=true&word_fields=text_uthmani&fields=text_uthmani,text_imlaei")['verse']
    c = get(f"https://api.alquran.cloud/v1/ayah/{s}:{v}/editions/quran-uthmani,ru.kuliev")['data']
    ru = q['translations'][0]['text']
    end = q['words'][-1]; assert end['char_type_name'] == 'end'
    assert ru == c[1]['text'], f"{s}:{v} Kuliev differs between sources"
    ac = c[0]['text']
    if v == 1 and s not in (1, 9):  # alquran.cloud prepends the basmala to the first ayah of a surah
        bas = get("https://api.alquran.cloud/v1/ayah/1:1/editions/quran-uthmani")['data'][0]['text']
        assert norm(ac).startswith(norm(bas) + ' '), f"{s}:{v} expected basmala prefix"
        ac = norm(ac)[len(norm(bas)) + 1:]
    assert norm(q['text_uthmani']) == norm(ac), f"{s}:{v} Arabic differs between sources"
    ayat.append(dict(key=f"{s}:{v}", ayah=v, uthmani=q['text_uthmani'].strip(), imlaei=q['text_imlaei'].strip(), end=end['text_uthmani'], ru=ru,
                     start=tim[v]['start_time'] / 1000, stop=tim[v]['end_time'] / 1000))
os.makedirs(f"src/{name}", exist_ok=True)
json.dump(dict(read=rid, reciter=reads[rid]['name'], surah=s, ayat=ayat), open(f"src/{name}/ayat.json", "w"), ensure_ascii=False, indent=1)
mp3 = f"src/{name}/{s:03d}.mp3"
if not os.path.exists(mp3):
    subprocess.run(["curl", "-sfL", "-o", mp3, reads[rid]['folder_url'] + f"{s:03d}.mp3"], check=True)
print(name, reads[rid]['name'], [(x['key'], round(x['start'], 2), round(x['stop'], 2)) for x in ayat])
