"""Photos: detect faces (tiled, multi-scale), write boxes.json + a first blurred PNG per photo.
Then review low-score boxes by hand and run photos_apply.py (keep list + manual extras).
  python3 photos.py SRC_DIR OUT_DIR"""
import sys, glob, os, json, numpy as np, cv2
import pillow_heif; pillow_heif.register_heif_opener()
from PIL import Image, ImageOps
sys.path.insert(0,os.path.dirname(__file__)); from blur import blur_faces
from insightface.app import FaceAnalysis
app=FaceAnalysis(name='buffalo_l',allowed_modules=['detection'],providers=['CPUExecutionProvider'])
app.prepare(ctx_id=-1,det_size=(640,640),det_thresh=0.25); det=app.det_model
src,dst=sys.argv[1],sys.argv[2]; os.makedirs(dst,exist_ok=True)
allb={}
for f in sorted(glob.glob(src+'/IMG_*.[HJ]*')):
    im=ImageOps.exif_transpose(Image.open(f)).convert('RGB')
    a=cv2.cvtColor(np.array(im),cv2.COLOR_RGB2BGR); H,W=a.shape[:2]
    boxes=[]
    for scale_tiles in (1,2,3,4):
        tw=int(np.ceil(W/scale_tiles*1.25)); th=int(np.ceil(H/scale_tiles*1.25))
        xs=np.linspace(0,W-tw,scale_tiles).astype(int) if scale_tiles>1 else [0]
        ys=np.linspace(0,H-th,scale_tiles).astype(int) if scale_tiles>1 else [0]
        for y in ys:
            for x in xs:
                t=np.ascontiguousarray(a[y:y+min(th,H),x:x+min(tw,W)])
                b,_=det.detect(t,input_size=(640,640) if scale_tiles>1 else (960,1280),max_num=0,metric='default')
                for bb in b: boxes.append([bb[0]+x,bb[1]+y,bb[2]+x,bb[3]+y,float(bb[4])])
    from track import nms
    boxes=nms([b for b in boxes if b[4]>=0.25])
    allb[os.path.basename(f)]=[[float(v) for v in b] for b in boxes]
    out=blur_faces(a,[b[:4] for b in boxes])
    name=os.path.splitext(os.path.basename(f))[0]
    cv2.imwrite(f'{dst}/{name}.png',out)
    print(name,W,H,len(boxes),flush=True)
json.dump(allb,open(dst+'/boxes.json','w'))
