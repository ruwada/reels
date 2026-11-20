"""Apply the face mask (track.py output) to the video: 1080x1920, 30 fps, CRF 10, original audio.
  python3 render_blur.py SRC.MOV MASK.json OUT.mp4"""
import sys, os, json, subprocess, numpy as np
sys.path.insert(0,os.path.dirname(__file__))
from blur import blur_faces
src, boxes_json, out = sys.argv[1:4]
B=json.load(open(boxes_json)); W,H=1080,1920
from common import vf_for
vf=vf_for(src)+",scale=1080:1920:flags=lanczos,eq=contrast=1.06:saturation=1.08,format=bgr24"
p=subprocess.Popen(['ffmpeg','-v','error','-i',src,'-vf',vf,'-f','rawvideo','-'],stdout=subprocess.PIPE)
e=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s','1080x1920','-r','30','-i','-','-i',src,'-map','0:v','-map','1:a','-c:v','libx264','-crf','10','-preset','medium','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','192k','-shortest',out],stdin=subprocess.PIPE)
i=0
while True:
    buf=p.stdout.read(W*H*3)
    if len(buf)<W*H*3: break
    f=np.frombuffer(buf,np.uint8).reshape(H,W,3).copy()
    f=blur_faces(f,B.get(str(i),[]))
    e.stdin.write(f.tobytes()); i+=1
e.stdin.close(); e.wait(); print('frames',i)
