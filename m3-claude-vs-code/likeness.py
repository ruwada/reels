# Speaker likeness: cosine of each take to the user's real voice (reels 18-24), 3D-Speaker ERes2Net via sherpa-onnx.
import sherpa_onnx, numpy as np, subprocess, glob, json, sys
ext = sherpa_onnx.SpeakerEmbeddingExtractor(sherpa_onnx.SpeakerEmbeddingExtractorConfig(model='/tmp/spk.onnx', num_threads=4))
def emb(f):
    pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', f, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout
    s = ext.create_stream(); s.accept_waveform(16000, np.frombuffer(pcm, np.float32)); s.input_finished()
    e = np.array(ext.compute(s)); return e / np.linalg.norm(e)
ref = [emb(f) for f in sorted(glob.glob('/mnt/project-files/voice/klon-mic/r*.mp3'))]
c = np.mean(ref, 0); c /= np.linalg.norm(c)
out = {}
for f in sys.argv[1:]:
    out[f] = round(float(emb(f) @ c), 3)
print(json.dumps(out, indent=0))
json.dump(out, open('likeness.json', 'w'), indent=0)
