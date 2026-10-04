#!/usr/bin/env python3
"""Find and fetch B-roll videos and photos from Pixabay (a second stock source next to pexels.py).

    python3 pixabay.py search "man typing laptop" [more queries...]
    python3 pixabay.py get 12893567 broll/        # saves broll/pixabay-12893567.mp4
    python3 pixabay.py photos "server room" [more queries...]
    python3 pixabay.py photo 8123456 img/         # saves img/pixabay-8123456.jpg (up to 1280 px)

The key comes from PIXABAY_API_KEY (the environment's variable).

Pixabay has no orientation filter for videos, so search keeps clips that are at least 1920 px tall:
portrait ones (P) fit as is, 4K landscape ones (L) get centre-cropped by render.py.
Same B-roll rules as Pexels: titles/tags are not enough, look at several frames of every clip,
and grep */edit.json for "pixabay-<id>" so a clip is never reused.
"""
import json, os, re, sys, urllib.parse, urllib.request

API = "https://pixabay.com/api/"
SKIP = re.compile(r"wom[ae]n|girl|lady|female|mother|bride|couple|family|kid|child|wine|beer|bar\b|party|dance|bikini|beach", re.I)


def call(path="videos/", **params):
    q = urllib.parse.urlencode({"key": os.environ["PIXABAY_API_KEY"], **params})
    return json.load(urllib.request.urlopen(urllib.request.Request(f"{API}{path}?{q}", headers={"User-Agent": "reels"})))


def download(url, path):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "reels"})) as r, open(path, "wb") as out:
        out.write(r.read())
    print(path)


def best_file(hit):
    """Smallest rendition at least 1920 px tall, portrait first."""
    files = [f for f in hit["videos"].values() if f.get("url") and f["height"] >= 1920]
    if not files:
        return None
    return min(files, key=lambda f: (f["width"] >= f["height"], f["height"]))


def search(query, n=20):
    for h in call(q=query, per_page=n, safesearch="true")["hits"]:
        f = best_file(h)
        if f and not SKIP.search(h["tags"] + " " + h["pageURL"]):
            kind = "P" if f["width"] < f["height"] else "L"
            print(f"{h['id']:>10} {h['duration']:>3}s {kind} {f['width']}x{f['height']}  {h['tags'][:60]}")


def get(vid, outdir):
    hits = call(id=vid)["hits"]
    f = best_file(hits[0]) if hits else None
    if not f:
        sys.exit(f"{vid}: no rendition at least 1920 px tall")
    os.makedirs(outdir, exist_ok=True)
    download(f["url"], os.path.join(outdir, f"pixabay-{vid}.mp4"))


def photos(query, n=20):
    for h in call("", q=query, per_page=n, image_type="photo", safesearch="true")["hits"]:
        if not SKIP.search(h["tags"] + " " + h["pageURL"]):
            ai = " AI" if h.get("isAiGenerated") else ""
            print(f"{h['id']:>10} {h['imageWidth']}x{h['imageHeight']}{ai}  {h['tags'][:60]}")


def photo(pid, outdir):
    hits = call("", id=pid)["hits"]
    if not hits:
        sys.exit(f"{pid}: not found")
    os.makedirs(outdir, exist_ok=True)
    download(hits[0]["largeImageURL"], os.path.join(outdir, f"pixabay-{pid}.jpg"))


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:]
    if cmd == "search":
        for query in rest:
            print(f"== {query}")
            search(query)
    elif cmd == "get":
        get(rest[0], rest[1] if len(rest) > 1 else ".")
    elif cmd == "photos":
        for query in rest:
            print(f"== {query}")
            photos(query)
    elif cmd == "photo":
        photo(rest[0], rest[1] if len(rest) > 1 else ".")
