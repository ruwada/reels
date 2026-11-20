"""Third pass: head boxes from YOLO pose keypoints for people whose face side is visible
(nose/eye keypoint conf >= 0.25). Catches profiles and faces looking down that SCRFD misses;
backs of heads (no nose/eyes) are skipped.
  python3 pose.py SRC.MOV OUT.json START STEP     (e.g. 0 4 and 2 4 = every 2nd frame)"""
# head boxes from pose keypoints for people whose face side is (partly) visible
import sys, json, subprocess, numpy as np, torch
torch.set_num_threads(1)
from ultralytics import YOLO
src,out,start,step=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
import os
m=YOLO(os.environ.get('POSE_MODEL','yolo11x-pose.pt'))  # downloads from GitHub on first run
W,H=1080,1920
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import vf_for
vf=vf_for(src)+",scale=1080:1920,format=bgr24"
p=subprocess.Popen(['ffmpeg','-v','error','-i',src,'-vf',vf,'-f','rawvideo','-'],stdout=subprocess.PIPE)
res={}; i=-1
while True:
    buf=p.stdout.read(W*H*3)
    if len(buf)<W*H*3: break
    i+=1
    if i%step!=start: continue
    f=np.frombuffer(buf,np.uint8).reshape(H,W,3)
    r=m.predict(f,imgsz=1280,conf=0.15,verbose=False)[0]
    boxes=[]
    if r.keypoints is not None and len(r.keypoints):
        kp=r.keypoints.data.cpu().numpy(); bb=r.boxes.xyxy.cpu().numpy()
        for k,b in zip(kp,bb):
            face=k[0:3]; head=k[0:5]
            if face[:,2].max()<0.25: continue   # no nose/eyes visible -> back of head
            pts=head[head[:,2]>0.2][:,:2]
            if len(pts)==0: continue
            # head size: from shoulders if visible, else from box width
            sh=k[5:7]
            if (sh[:,2]>0.3).all(): s=np.linalg.norm(sh[0,:2]-sh[1,:2])*0.55
            else: s=(b[2]-b[0])*0.35
            s=max(s, np.ptp(pts[:,0])*1.3 if len(pts)>1 else 0, 18)
            cx,cy=pts[:,0].mean(),pts[:,1].mean()
            boxes.append([float(cx-s/2),float(cy-s*0.6),float(cx+s/2),float(cy+s*0.55),float(face[:,2].max())])
    res[i]=boxes
    if i%60==start: print(i,len(boxes),flush=True)
json.dump(res,open(out,'w'))
