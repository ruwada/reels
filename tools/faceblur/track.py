# link detections into tracks, interpolate gaps, hold ends -> per-frame mask boxes
import json, sys, numpy as np
def load(paths):
    d={}
    for p in paths:
        for k,v in json.load(open(p)).items(): d[int(k)]=v
    return d
def nms(boxes, thr=0.4):
    boxes=sorted(boxes,key=lambda b:-b[4]); keep=[]
    for b in boxes:
        ok=True
        for k in keep:
            ix=max(0,min(b[2],k[2])-max(b[0],k[0])); iy=max(0,min(b[3],k[3])-max(b[1],k[1]))
            inter=ix*iy; a=(b[2]-b[0])*(b[3]-b[1]); ak=(k[2]-k[0])*(k[3]-k[1])
            if inter/min(a,ak)>thr: ok=False;break
        if ok: keep.append(b)
    return keep
def build(det, nframes, thr=0.2, maxgap=20, hold=8):
    frames=sorted(det)
    tracks=[]  # list of dict frame->box
    for f in frames:
        bs=nms([b for b in det[f] if b[4]>=thr])
        used=set()
        cand=[]
        for ti,t in enumerate(tracks):
            lf=max(t); 
            if f-lf>maxgap: continue
            lb=t[lf]; cx=(lb[0]+lb[2])/2; cy=(lb[1]+lb[3])/2; s=max(lb[2]-lb[0],lb[3]-lb[1])
            for bi,b in enumerate(bs):
                bx=(b[0]+b[2])/2; by=(b[1]+b[3])/2; sb=max(b[2]-b[0],b[3]-b[1])
                dist=np.hypot(bx-cx,by-cy)
                if dist< s*(1.0+0.08*(f-lf)) and 0.5<sb/s<2: cand.append((dist/s,ti,bi))
        cand.sort(); tu=set()
        for _,ti,bi in cand:
            if ti in tu or bi in used: continue
            tracks[ti][f]=bs[bi][:4]; tu.add(ti); used.add(bi)
        for bi,b in enumerate(bs):
            if bi not in used: tracks.append({f:b[:4]})
    out={i:[] for i in range(nframes)}
    for t in tracks:
        ks=sorted(t)
        for a,b in zip(ks,ks[1:]):
            for f in range(a,b):
                r=(f-a)/(b-a); out[f].append([t[a][j]*(1-r)+t[b][j]*r for j in range(4)])
        out.setdefault(ks[-1],[]).append(t[ks[-1]])
        for f in range(ks[0]-hold,ks[0]):
            if 0<=f<nframes: out[f].append(t[ks[0]])
        for f in range(ks[-1]+1,ks[-1]+hold+1):
            if 0<=f<nframes: out[f].append(t[ks[-1]])
    # also union with raw dets of neighbours +-2 (fast motion safety)
    for f in range(nframes):
        for g in range(f-2,f+3):
            for b in det.get(g,[]):
                if b[4]>=thr: out[f].append(b[:4])
    return out, len(tracks)
if __name__=='__main__':
    det=load(sys.argv[3:]); n=int(sys.argv[2])
    out,nt=build(det,n)
    json.dump(out,open(sys.argv[1],'w')); print('tracks',nt)
