import json,sys,urllib.request,os
H={"User-Agent":"reels"}
for vid in sys.argv[1:]:
    p=f"broll/{vid}.mp4"
    if os.path.exists(p): continue
    v=json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.pexels.com/videos/videos/{vid}",headers=H)))
    fs=[f for f in v["video_files"] if f["width"] and f["width"]<f["height"]]
    f=max(fs,key=lambda f:f["height"])
    with urllib.request.urlopen(urllib.request.Request(f["link"],headers=H)) as r, open(p,"wb") as o: o.write(r.read())
    print(vid,f["width"],f["height"],v["duration"])
