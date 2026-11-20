# Method 3: reels built from code

Motion-graphics reels and inserts rendered from HTML (HyperFrames) or React (Remotion): kinetic titles,
animated numbers, checklists, chat mock-ups, CTA plates. Output 1080x1920 MP4, no footage needed; the
same compositions can also be laid over the author's talking-head video.

    setup.sh                       installs HyperFrames, impeccable, frontend-design (plugins),
                                   Remotion, taste-skill, Emil Kowalski skills, video-use (skills)
    template/                      9:16 HyperFrames project: local GSAP, Unbounded + Manrope (latin + cyrillic),
                                   4 scenes (hook, number card, checklist, CTA) inside the safe zones
    preview.sh                     contact sheet of a render with the safe zones drawn on top
    ramka-instagram-1080x1920.png  transparent safe-zone frame for any editor

## Making a reel

    bash tools/code-video/setup.sh                 # once per fresh container
    cp -r tools/code-video/template NN-name/code   # NN-name = the reel's folder
    cd NN-name/code && npm run check && npm run render
    bash ../../tools/code-video/preview.sh renders/reel.mp4 2 5 9 12

Safe zones (Instagram Reels UI): keep text out of the top 200 px, bottom 320 px and right 130 px; the
handle and caption cover everything below 1190 px, so key content sits between 200 and 1190.

Environment notes: cdn.jsdelivr.net and remotion.media are blocked by the proxy, so GSAP ships in
`template/assets/` and Remotion renders with
`--browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`.
Remotion is free for individuals and companies of up to 3 people. video-use transcribes through
ElevenLabs Scribe and spends that account's credits; the free local option is `tools/transcribe.py`.
