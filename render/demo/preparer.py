import json,hashlib,subprocess as sp,os
from pathlib import Path as P
J=lambda s:json.loads(P(s).read_text());m=J('render/demo/plans.json');d=P('work');d.mkdir(exist_ok=True);src=d/'source.mp4';F=os.getenv('FFMPEG','ffmpeg');
if not src.exists():sp.run(['curl','--fail','-LsS','--retry','3',m['source'],'-o',str(src)],check=True)
assert hashlib.sha256(src.read_bytes()).hexdigest()==m['sha256'];plan=J('montage/partition.json')
for s,sc in zip(m['plans'],plan['scenes']):
 frames=sc['fin']-sc['debut'];fps=plan['fps'];w,h=plan['dimensions'];vf=f"crop=trunc(ih*{w}/{h}/2)*2:ih:iw*{s['centre']}-ow/2:0,scale={w}:{h},setsar=1,setpts=(PTS-STARTPTS)*{frames/fps/s['longueur']},fps={fps},tpad=stop_mode=clone:stop_duration=0.25";sp.run([F,'-loglevel','error','-y','-ss',str(s['debut']),'-t',str(s['longueur']),'-i',str(src),'-an','-vf',vf,'-frames:v',str(frames),'-c:v','libx264','-threads','3','-preset','fast','-crf','16','-pix_fmt','yuv420p',str(d/(sc['id']+'.mp4'))],check=True)
