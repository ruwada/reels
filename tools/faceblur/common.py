import json, subprocess
def probe(src):
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=width,height,color_transfer:stream_side_data=rotation', '-of', 'json', src],
        capture_output=True, text=True).stdout)['streams'][0]
    return j
def probe_wh(src):
    j = probe(src); w, h = j['width'], j['height']
    rot = abs(int(next((s.get('rotation', 0) for s in j.get('side_data_list', [])), 0)))
    return (h, w) if rot in (90, 270) else (w, h)
def vf_for(src, fps=30):
    """Decode filter: 30 fps, HLG (iPhone) -> SDR bt709 tonemap; plain SDR passes through."""
    if probe(src).get('color_transfer') == 'arib-std-b67':
        return (f"fps={fps},zscale=tin=arib-std-b67:npl=150,zscale=t=linear:npl=150,format=gbrpf32le,"
                "zscale=p=bt709,tonemap=mobius,zscale=t=bt709:m=bt709:r=pc,format=gbrp")
    return f"fps={fps},format=gbrp"
