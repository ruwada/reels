import cv2, numpy as np
def blur_faces(img, boxes, padw=0.6, padh=0.75):
    h,w=img.shape[:2]
    if not boxes: return img
    mask=np.zeros((h,w),np.uint8)
    for b in boxes:
        x0,y0,x1,y1=b; bw=x1-x0; bh=y1-y0
        if bw<=1 or bh<=1: continue
        cx=(x0+x1)/2; cy=(y0+y1)/2-bh*0.05
        ax=bw*(1+padw)/2+4; ay=bh*(1+padh)/2+4
        cv2.ellipse(mask,(int(cx),int(cy)),(int(ax),int(ay)),0,0,360,255,-1)
    # strong anonymisation: coarse mosaic + very heavy gaussian (irreversible)
    s=max(12,int(min(w,h)/45))
    small=cv2.resize(img,(max(1,w//s),max(1,h//s)),interpolation=cv2.INTER_AREA)
    mos=cv2.resize(small,(w,h),interpolation=cv2.INTER_LINEAR)
    k=int(min(w,h)/14)|1
    bl=cv2.GaussianBlur(mos,(k,k),0)
    soft=cv2.GaussianBlur(mask,(15,15),0)
    m=np.maximum(soft,mask).astype(np.float32)[...,None]/255
    return (img*(1-m)+bl*m).astype(np.uint8)
