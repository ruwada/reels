import cv2, numpy as np, sys, os
v,out,step,start=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
os.makedirs(out,exist_ok=True)
cap=cv2.VideoCapture(v); fr=[]; n=0
while True:
    ok,f=cap.read()
    if not ok: break
    if n%step==start:
        s=cv2.resize(f,(450,800)); cv2.putText(s,str(n),(10,30),0,1,(0,255,255),2); fr.append(s)
    n+=1
for i in range(0,len(fr),6):
    row=fr[i:i+6]
    while len(row)<6: row.append(np.zeros_like(fr[0]))
    cv2.imwrite(f'{out}/s{i//6:02d}.jpg',np.hstack(row),[cv2.IMWRITE_JPEG_QUALITY,88])
