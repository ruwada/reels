"""Face detection (insightface SCRFD) on every frame of an iPhone HLG/SDR video.
Writes {frame: [[x0,y0,x1,y1,score], ...]} in 1080x1920 output coordinates.
  python3 det.py SRC.MOV OUT.json START STEP [--pad]
START/STEP split the work between processes (e.g. 0 2 and 1 2).
--pad: second pass on a black-padded frame with threshold 0.2 (catches faces cut by the frame edge;
       track.py keeps its low-score boxes only near the edges)."""
import sys, json, subprocess, numpy as np
from insightface.app import FaceAnalysis
from common import vf_for, probe_wh
src, out, start, step = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
PAD = '--pad' in sys.argv
W, H = probe_wh(src)              # display size after rotation (e.g. 2160x3840)
app = FaceAnalysis(name='buffalo_l', allowed_modules=['detection'], providers=['CPUExecutionProvider'])
app.prepare(ctx_id=-1, det_size=(640, 640), det_thresh=0.2 if PAD else 0.3)
det = app.det_model
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-vf', vf_for(src) + ',scale=1080:1920,format=bgr24',
                      '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
res = {}; i = -1; FW, FH = 1080, 1920
while True:
    buf = p.stdout.read(FW * FH * 3)
    if len(buf) < FW * FH * 3: break
    i += 1
    if i % step != start: continue
    f = np.frombuffer(buf, np.uint8).reshape(FH, FW, 3)
    boxes = []
    if PAD:
        P = 192
        pad = np.zeros((FH + 2 * P, FW + 2 * P, 3), np.uint8); pad[P:P + FH, P:P + FW] = f
        b, _ = det.detect(pad, input_size=(1472, 2304), max_num=0)
        boxes = [[x0 - P, y0 - P, x1 - P, y1 - P, s] for x0, y0, x1, y1, s in b]
    else:
        b, _ = det.detect(np.ascontiguousarray(f), input_size=(1088, 1920), max_num=0)
        boxes = [list(x) for x in b]
    res[i] = [[round(float(v), 1) for v in bb[:4]] + [round(float(bb[4]), 3)] for bb in boxes]
    if i % 60 == start: print(i, len(boxes), flush=True)
json.dump(res, open(out, 'w'))
