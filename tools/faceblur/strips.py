import cv2, sys, numpy as np
v,a,b,st,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
cap=cv2.VideoCapture(v); L=[];R=[]
for n in range(a,b,st):
    cap.set(cv2.CAP_PROP_POS_FRAMES,n); ok,f=cap.read()
    if not ok: break
    f=cv2.resize(f,(540,960))
    l=f[:, :170].copy(); r=f[:, 370:].copy()
    for s in (l,r): cv2.putText(s,str(n),(5,25),0,0.8,(0,255,255),2)
    L.append(l); R.append(r)
cv2.imwrite(out+'_L.jpg',np.hstack(L)); cv2.imwrite(out+'_R.jpg',np.hstack(R))
