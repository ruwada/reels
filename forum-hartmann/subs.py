import json,unicodedata,re
V=json.load(open('work/voice_tl.json')); L=V['lines']; s=[l['start'] for l in L]
def strip(t): return unicodedata.normalize('NFC',''.join(c for c in unicodedata.normalize('NFD',t) if c!='\u0301'))
def words(i):
    a=json.load(open(f'tts/p{i}.json')); ch=a['characters']; st=a['character_start_times_seconds']; en=a['character_end_times_seconds']
    out=[];cur='';t0=None;t1=None
    for c,x,y in zip(ch,st,en):
        if c=='́': continue
        if c.isspace():
            if cur: out.append([cur,t0,t1]); cur=''
            continue
        if not cur: t0=x
        cur+=c; t1=y
    if cur: out.append([cur,t0,t1])
    return [[strip(w),s[i]+a_,s[i]+b_] for w,a_,b_ in out if strip(w) not in ('—','-')]
REP={'эй-ай-пилотов':'AI-пилотов','эй-ай-агентов':'AI-агентов','эй-ай-агенты':'AI-агенты','эй-ай-продавцы':'AI-продавцы','эй-ай.':'AI.','эм-ай-ти.':'MIT.','пятого':'5'}
def disp(ws):
    o=[]
    k=0
    while k<len(ws):
        w,a,b=ws[k]
        if w=='Девяносто': o.append(['95%',a,ws[k+2][2]]); k+=3; continue
        o.append([REP.get(w,w).replace('«','').replace('»',''),a,b]); k+=1
    return o
def chunks(ws):
    out=[];cur=[]
    for w in ws:
        cur.append(w)
        if len(cur)==3 or (len(cur)>=2 and len(' '.join(x[0] for x in cur))>14) or w[0][-1] in '.,:!?':
            out.append(cur);cur=[]
    if cur: out.append(cur)
    return out
def ts(t):
    t=max(0,t); h=int(t//3600); m=int(t%3600//60); return f"{h}:{m:02d}:{t%60:05.2f}"
b=json.load(open('work/bounds.json'))['b'] if False else None
HIDE=None
hdr="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: RU,Inter ExtraBold,74,&H00FFFFFF,&H00FFFFFF,&H183A1610,&H00000000,0,0,0,0,100,100,0,0,3,16,0,5,0,0,0,1
Style: EN,Inter SemiBold,40,&H00B0D8FF,&H00FFFFFF,&H283A1610,&H00000000,0,0,0,0,100,100,0,0,3,10,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
import sys
hide=json.loads(sys.argv[1]) if len(sys.argv)>1 else [0,0]
ev=[]
allch=[c for i in range(len(L)) for c in chunks(disp(words(i)))]
for ci,ch in enumerate(allch):
    if True:
        for j,(w,a,e) in enumerate(ch):
            end=ch[j+1][1] if j+1<len(ch) else (min(e+0.12,allch[ci+1][0][1]) if ci+1<len(allch) else e+0.3)
            if a>=hide[0] and a<hide[1]: continue
            txt=' '.join((r'{\c&H004D7AFF&}'+x+r'{\c&H00FFFFFF&}') if k==j else x for k,(x,_,_) in enumerate(ch))
            ev.append(f"Dialogue: 0,{ts(a)},{ts(end)},RU,,0,0,0,,{{\\pos(475,1030)}}{txt}")
EN=[("95% of AI pilots make no money","Это","That's MIT data"),("I build AI agents for business","инструме","Tool bought, leads still done by hand"),
("Dec 5 I'll be in Istanbul","на фо","at Oskar Hartmann's AI forum"),("Morning: talks on trends and markets","После","Afternoon: three practice halls"),
("Sales: AI agents that bring revenue",None,None),("Management: AI sellers take the routine",None,None),("Brand: promote yourself with AI",None,None),
("Mentor lounge: ask speakers in person","Организа","Promised: leave with a plan. I'll check"),("Going for cases, contacts, projects",None,None),
("I'll bring the best here. Follow","А е","Coming too? Write me, see you there")]
for i,(e1,key,e2) in enumerate(EN):
    a=json.load(open(f'tts/p{i}.json')); txt=''.join(a['characters']); st=a['character_start_times_seconds']; end=s[i]+a['character_end_times_seconds'][-1]+0.12
    if key:
        k=txt.find(key); m=s[i]+st[k]; parts=[(s[i],m,e1),(m,end,e2)]
    else: parts=[(s[i],end,e1)]
    for x,y,t in parts:
        if x>=hide[0] and x<hide[1]: continue
        if x<hide[0]<y: y=hide[0]
        ev.append(f"Dialogue: 0,{ts(x)},{ts(y)},EN,,0,0,0,,{{\\pos(475,1125)}}{t}")
open('work/subs.ass','w').write(hdr+'\n'.join(ev)+'\n'); print(len(ev))
