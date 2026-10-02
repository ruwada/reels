import subprocess
S="/tmp/claude-0/hay/screen.mp4"
def run(a): subprocess.run(["ffmpeg","-v","error","-y",*a],check=True)
def zoomchain(dur,fy,z0,z1,iw=1080,ih0=2337):
    # scale whole frame to width 1080*z(t), crop 1080x1920 around focus fy
    z=f"({z0}+({z1}-{z0})*t/{dur})"
    return (f"scale=w='trunc(1080*{z}/2)*2':h=-2:eval=frame:flags=lanczos,"
            f"crop=1080:1920:x='(iw-1080)/2':y='max(0,min(ih-1920,{fy}*ih-960))'")
def screen(name,t0,dur,fy,z0=1.0,z1=1.06,speed=1.0):
    src_d=dur*speed
    run(["-ss",str(t0),"-t",f"{src_d:.3f}","-i",S,"-an","-vf",
         f"setpts=PTS/{speed},fps=30,{zoomchain(dur,fy,z0,z1)},setsar=1,format=yuv420p","-t",f"{dur:.3f}","-c:v","libx264","-crf","14",f"{name}.mp4"])
def still(name,img,dur,fy,z0=1.0,z1=1.06,ih0=2337):
    run(["-loop","1","-framerate","30","-t",f"{dur:.3f}","-i",img,"-vf",f"{zoomchain(dur,fy,z0,z1)},setsar=1,format=yuv420p","-c:v","libx264","-crf","14",f"{name}.mp4"])
def lockn(name,bg,n,dur):
    run(["-loop","1","-framerate","30","-t",f"{dur:.3f}","-i",bg,"-loop","1","-framerate","30","-t",f"{dur:.3f}","-i",n,"-filter_complex",
         "[1:v]format=rgba,fade=in:st=0.35:d=0.25:alpha=1[n];[0:v][n]overlay=x=0:y='if(lt(t,0.35),-400,-400*pow(max(0,1-(t-0.35)/0.35),3))':eval=frame,"
         f"{zoomchain(dur,0.5,1.0,1.04)},setsar=1,format=yuv420p","-c:v","libx264","-crf","14",f"{name}.mp4"])
def toggle(name,off,on,dur):
    run(["-loop","1","-framerate","30","-t",f"{dur:.3f}","-i",off,"-loop","1","-framerate","30","-t",f"{dur:.3f}","-i",on,"-filter_complex",
         "[1:v]format=rgba,fade=in:st=0.7:d=0.25:alpha=1[n];[0:v][n]overlay,"
         f"{zoomchain(dur,0.3,1.0,1.08)},setsar=1,format=yuv420p","-c:v","libx264","-crf","14",f"{name}.mp4"])
# frames for stills
run(["-ss","40.5","-i",S,"-frames:v","1","priv.png"])
run(["-ss","119","-i",S,"-frames:v","1","role.png"])
screen("c_dev",63,3.8,0.35,1.0,1.06)
screen("c_start",134.8,1.5,0.62,1.0,1.04)
screen("c_face",138.5,4.5,0.27,1.3,1.42)
screen("c_timer",139,4.5,0.5,1.0,1.06,speed=27)
screen("c_myt",111,2.8,0.3,1.15,1.22)
screen("c_coins",265,3.1,0.42,1.0,1.06)
screen("c_shop",270,3.3,0.6,1.0,1.06)
screen("c_parent",301,2.0,0.3,1.15,1.2)
screen("c_hist",306,2.0,0.4,1.0,1.05)
still("c_priv","priv.png",5.0,0.2,1.35,1.5)
still("c_role","role.png",1.9,0.6,1.2,1.28)
lockn("c_alarm","lock_child.png","n_child.png",2.2)
lockn("c_missed","lock_parent.png","n_parent.png",4.2)
toggle("c_tyagi","tyagi_off.png","tyagi_on.png",4.0)
still("c_store","store.png",2.9,0.5,1.0,1.04)
