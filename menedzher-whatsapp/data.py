# tts/pN.json + gaps -> data.json (words with line/k, line starts, END) + mix.wav
import json,subprocess,sys
G=json.load(open('gaps.json'))   # {"start":0.5,"gaps":[...],"tail":3}
n=len(json.load(open('lines.json')))
dur=[json.load(open(f'tts/p{i}.json'))['character_end_times_seconds'][-1] for i in range(n)]
L=[G['start']]
for i in range(n-1): L.append(L[-1]+dur[i]+G['gaps'][i])
END=round(L[-1]+dur[-1]+G['tail'],2)
words=[]
for i,o in enumerate(L):
    a=json.load(open(f'tts/p{i}.json'));ch=a['characters'];s=a['character_start_times_seconds'];e=a['character_end_times_seconds']
    w='';k=0
    for c,cs,ce in zip(ch+[' '],s+[0],e+[0]):
        if c==' ':
            if w: words.append([w,round(ws+o,3),round(we+o,3),i,k]);k+=1;w=''
            continue
        if not w: ws=cs
        w+=c;we=ce
DP=json.load(open('disp.json'))
for x in words: x[0]=DP[x[3]].split()[x[4]]
json.dump({'L':[round(x,3) for x in L],'END':END,'words':words},open('data.json','w'))
inp=[];fc=[]
for i in range(n): inp+=['-i',f'tts/p{i}.mp3'];fc.append(f'[{i}]adelay={int(L[i]*1000)}:all=1[a{i}]')
fc.append(''.join(f'[a{i}]' for i in range(n))+f'amix=inputs={n}:normalize=0,apad=whole_dur={END},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[o]')
subprocess.run(['ffmpeg','-v','error','-y']+inp+['-filter_complex',';'.join(fc),'-map','[o]','-t',str(END),'-c:a','pcm_s16le','mix.wav'],check=True)
print('L',[round(x,2) for x in L],'END',END)
for i in range(n): print(i,' '.join(f"{w[4]}:{w[0]}@{w[1]}" for w in words if w[3]==i))
