# add manually keyframed tracks (interpolated) to a mask json
import json, sys
mask=json.load(open(sys.argv[1])); man=json.load(open(sys.argv[2]))
for tr in man.get(sys.argv[3],[]):
    ks=sorted(int(k) for k in tr)
    for a,b in zip(ks,ks[1:]):
        for f in range(a,b+1):
            r=(f-a)/(b-a); box=[tr[str(a)][j]*(1-r)+tr[str(b)][j]*r for j in range(4)]
            mask.setdefault(str(f),[]).append(box)
json.dump(mask,open(sys.argv[1],'w'))
