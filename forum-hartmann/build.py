import json,subprocess,os,unicodedata
V=json.load(open('work/voice_tl.json')); L=V['lines']; TOT=V['total']
s=[l['start'] for l in L]
def tsplit(i,key):
    a=json.load(open(f'tts/p{i}.json')); txt=''.join(a['characters']); k=txt.find(key); assert k>=0,(i,key)
    return s[i]+a['character_start_times_seconds'][k]
b=[0, s[1]-.1, tsplit(1,':')+.05, s[2]-.1, tsplit(2,'на фо')-.05, s[3]-.1, tsplit(3,'три за')-.05, s[4]-.1, s[5]-.1, s[6]-.1, s[7]-.1, s[8]-.1, s[9]-.1, TOT]
CL=[('6100413',17.5),('30284959',2),('7279035',3),('34883124',13),('38924323',15),('8348725',1),('HALLS',0),('35417425',10),('7706761',1),('8264022',5),('8348721',1),('34467289',2),('40803927',2)]
TR=['fadeblack','slideup','zoomin','dissolve','wipeleft','fade','slideleft','slideup','slideleft','circleopen','fadewhite','dissolve']
D=0.35; os.makedirs('work/seg',exist_ok=True)
for k,(c,inp) in enumerate(CL):
    dur=b[k+1]-b[k]+(D if k<len(CL)-1 else 0); out=f'work/seg/{k:02d}.mp4'
    if c=='HALLS':
        src=['-loop','1','-t',f'{dur:.3f}','-i','gfx/halls.png']; vf=f"scale=1188:2112,crop=1080:1920:x='54-54*t/{dur:.3f}':y='96-96*t/{dur:.3f}'"
    else:
        src=['-ss',str(inp),'-t',f'{dur:.3f}','-i',f'broll/{c}.mp4']
        vf=f"scale=1188:-2:flags=lanczos,crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*(0.2+0.6*t/{dur:.3f})',eq=contrast=1.04:saturation=1.06"
    if os.path.exists(out): continue
    subprocess.run(['ffmpeg','-v','error','-y',*src,'-vf',vf+',fps=30,format=yuv420p','-an','-c:v','libx264','-crf','12','-preset','fast',out],check=True)
# xfade chain
inp=[];
for k in range(len(CL)): inp+=['-i',f'work/seg/{k:02d}.mp4']
f=[];prev='[0:v]'
for k in range(1,len(CL)):
    o=f'[x{k}]'; f.append(f'{prev}[{k}:v]xfade=transition={TR[k-1]}:duration={D}:offset={b[k]:.3f}{o}'); prev=o
# overlays
ov=[('p95',0.15,b[1]-0.2),('title',b[4]+0.25,b[5]-0.15),('h1',b[7]+0.2,b[8]-0.1),('h2',b[8]+0.25,b[9]-0.1),('h3',b[9]+0.25,b[10]-0.1),('cta',s[9]+0.2,TOT)]
n=len(CL)
for j,(name,a,e) in enumerate(ov):
    inp+=['-loop','1','-t',f'{TOT:.3f}','-i',f'gfx/{name}.png']
    f.append(f'[{n+j}:v]format=rgba,fade=in:st={a:.3f}:d=0.3:alpha=1,fade=out:st={e-0.25:.3f}:d=0.25:alpha=1[o{j}]')
    o=f'[y{j}]'; f.append(f'{prev}[o{j}]overlay=0:0:enable=\'between(t,{a:.3f},{e:.3f})\'{o}'); prev=o
f.append(f"{prev}subtitles=work/subs.ass:fontsdir=gfx,format=yuv420p[v]")
inp+=['-i','work/voice.wav']
subprocess.run(['ffmpeg','-v','error','-y',*inp,'-filter_complex',';'.join(f),'-map','[v]','-map',f'{n+len(ov)}:a','-t',f'{TOT:.3f}','-c:v','libx264','-crf','14','-preset','slow','-profile:v','high','-c:a','aac','-b:a','192k','-movflags','+faststart','work/master.mp4'],check=True)
json.dump({'b':b,'s':s},open('work/bounds.json','w'))
print('ok',b)
