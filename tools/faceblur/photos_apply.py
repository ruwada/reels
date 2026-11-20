"""Final photo blur: boxes with score>=0.5 + hand-picked low-score boxes (photos_keep.json)
+ manual boxes (photos_extra.json, {photo: [[x0,y0,x1,y1],...]}). Expects M/src and M/photos_blur.
  python3 photos_apply.py M"""
import json, os, sys, cv2, numpy as np
import pillow_heif; pillow_heif.register_heif_opener()
from PIL import Image, ImageOps
sys.path.insert(0,os.path.dirname(__file__)); from blur import blur_faces
M=sys.argv[1]
d=json.load(open(M+'/photos_blur/boxes.json'))
# keep.json: {photo: [indexes of low-score (<0.5) boxes that ARE faces]}, chosen by hand from a crop grid
keep=json.load(open(M+'/photos_keep.json')) if os.path.exists(M+'/photos_keep.json') else {}
extra=json.load(open(M+'/photos_extra.json')) if os.path.exists(M+'/photos_extra.json') else {}
final={}
for k,v in d.items():
    bs=[b[:4] for i,b in enumerate(v) if b[4]>=0.5 or i in keep.get(k,[])]+extra.get(k,[])
    final[k]=bs
    im=ImageOps.exif_transpose(Image.open(M+'/src/'+k)).convert('RGB')
    a=cv2.cvtColor(np.array(im),cv2.COLOR_RGB2BGR)
    cv2.imwrite(M+'/photos_blur/'+os.path.splitext(k)[0]+'.png',blur_faces(a,bs))
    print(k,len(bs))
json.dump(final,open(M+'/photos_blur/final_boxes.json','w'))
