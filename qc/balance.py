"""Mesure sur le film livré : projection du PCM AAC sur les deux sources connues, par fenêtres actives de 100 ms."""
import sys,os,json,numpy as np
from pathlib import Path as P
sys.path.insert(0,'audio');from mixer import decode,level,R,H,I
film,mp3=sys.argv[1:3];assert H(film)=='81256318e4fc297f33da56f8d2083f0517917040c0c7a0533bd4654187ae9b99';v=decode('render/demo/voix/T5-Voix-seule.wav');m=decode(mp3)[round(.38*R):][:len(v)];y=decode(film)[:len(v)];by={};err=[]
for c in I('render/demo/voix/calage.json'):
 vs=ms=0
 for n in range(round(c['debut_s']*R),round(c['fin_s']*R)-4800,4800):
  a,b,o=[z[n:n+4800].flatten().astype(float) for z in (v,m,y)];
  if np.mean(a*a)<.0001:continue
  A=np.column_stack([a,b]);g=np.linalg.lstsq(A,o,rcond=None)[0];vs+=sum((a*g[0])**2);ms+=sum((b*g[1])**2);err.append(np.mean((A@g-o)**2)/np.mean(o**2))
 by[c['scene']]=round(10*np.log10(vs/ms),2)
li,tp=level(y);rep=dict(lufs=li,true_peak=tp,ecart_par_scene_db=by,residu_median=float(np.median(err)),sha256=H(film));print(json.dumps(rep));assert min(by.values())>=4 and abs(li+16)<.75 and tp<=-1 and np.median(err)<.08
