set -e
B=../broll; A0=7870.17; AD=47.45; B1=22.89; T=48.65
ffmpeg -v error -y \
 -i $B/35825483.mp4 -i $B/36259621.mp4 -i $B/28956194.mp4 \
 -ss $A0 -t $AD -i ../src/002-raad.mp3 \
 -loop 1 -t $T -i mask-1.png -loop 1 -t $T -i text-1.png -loop 1 -t $T -i text-2.png -loop 1 -t $T -i wm.png \
 -filter_complex "
 [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,trim=0:12.9,setpts=PTS-STARTPTS,format=yuv420p[v0];
 [1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,trim=0:12.8,setpts=PTS-STARTPTS,format=yuv420p[v1];
 [2:v]setpts=1.19*PTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p[v2];
 [v0][v1]xfade=transition=fade:duration=0.8:offset=12.1[x1];
 [x1][v2]xfade=transition=fade:duration=0.8:offset=24.1,trim=0:$T,setpts=PTS-STARTPTS,eq=brightness=0.02:saturation=1.05[bg];
 [bg]split[bgA][bgB];
 [bgB]gblur=sigma=18,format=rgba[bl];[4:v]format=gray[mk];[bl][mk]alphamerge,fade=t=in:st=0:d=0.6:alpha=1,fade=t=out:st=47.6:d=0.5:alpha=1[blm];
 [bgA][blm]overlay=0:0[b2];
 [5:v]format=rgba,fade=t=in:st=0:d=0.6:alpha=1,fade=t=out:st=$(echo "$B1-0.3"|bc):d=0.25:alpha=1[t1];
 [6:v]format=rgba,fade=t=in:st=$B1:d=0.3:alpha=1,fade=t=out:st=47.6:d=0.5:alpha=1[t2];
 [b2][t1]overlay=0:0:enable='lt(t,$B1+0.3)'[b3];[b3][t2]overlay=0:0:enable='gte(t,$B1-0.3)'[b4];
 [b4][7:v]overlay=0:0,fade=t=out:st=48.0:d=0.65,format=yuv420p[v];
 [3:a]afade=t=in:d=0.1,afade=t=out:st=$(echo "$AD-0.25"|bc):d=0.25,apad=whole_dur=$T[a]" \
 -map "[v]" -map "[a]" -t $T -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart quran-2-268-269.mp4
