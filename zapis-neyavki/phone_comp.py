# usage: phone_comp.py <phone.mp4> <ss> <chat.mp4> <out.mp4>
# Puts the chat animation onto the white screen of a real phone clip: per-frame screen rect from the white area,
# the white pixels themselves are the mask (keeps rounded corners, notch, any finger in front).
import cv2,numpy as np,subprocess,sys
ph,ss,ch,out=sys.argv[1],float(sys.argv[2]),sys.argv[3],sys.argv[4]
cp=cv2.VideoCapture(ph);cp.set(cv2.CAP_PROP_POS_MSEC,ss*1000)
cc=cv2.VideoCapture(ch);n=int(cc.get(cv2.CAP_PROP_FRAME_COUNT))
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s','1080x1920','-r','30','-i','-','-c:v','libx264','-crf','12','-preset','slow','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
for i in range(n):
    ok,f=cp.read();ok2,c=cc.read()
    if not ok or not ok2:break
    f=cv2.resize(f,(1080,1920))
    g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY);m=(g>170).astype(np.uint8)*255;m[:450]=0
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cn=max(cs,key=cv2.contourArea)
    keep=np.zeros_like(m);cv2.drawContours(keep,[cn],-1,255,-1);m=cv2.bitwise_and(m,keep)
    x,y,w,h=cv2.boundingRect(cn)
    a=np.zeros((1920,1080),np.float32);a[m>0]=1
    a=cv2.GaussianBlur(a,(3,3),0)[...,None]
    cz=cv2.resize(c,(w,h),interpolation=cv2.INTER_AREA)
    lay=f.copy();lay[y:y+h,x:x+w]=cz
    # keep a hint of the real screen's light falloff
    shade=(g.astype(np.float32)/255.0)[...,None];shade=0.9+0.1*np.clip(shade*1.1,0,1)
    o=(f*(1-a)+lay*shade*a).clip(0,255).astype(np.uint8)
    enc.stdin.write(o.tobytes())
enc.stdin.close();enc.wait();print('frames',i+1)
