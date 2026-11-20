"""Rendu silencieux d’un job navigateur. Aucun accès réseau ni texte de boutique figé."""
import argparse,hashlib,json,subprocess as sp,os
from pathlib import Path as P
from functools import lru_cache
import cv2 as cv,numpy as np
from PIL import Image,ImageFont,ImageDraw
J=lambda p:json.loads(P(p).read_text());H=lambda p:hashlib.sha256(P(p).read_bytes()).hexdigest()
e=J('catalogue/catalogue.json')['entries'][0];plan=J(e['partition']);scenes=plan['scenes'];W,Y=plan['dimensions'];FPS=plan['fps'];T=plan['texte'];F=os.getenv('FFMPEG','ffmpeg');cv.setNumThreads(2)
@lru_cache(None)
def font(n):
 f=ImageFont.truetype(T['fonte'],n);return f

def wrap(txt,f):
 lines=[];s=''
 for word in txt.split():
  add=(s+' '+word).strip()
  if s and f.getlength(add)>T['largeur']:lines.append(s);s=word
  else:s=add
 if s:lines.append(s)
 return lines

def overlay(c,rep):
 im=Image.new('RGBA',(W,Y));d=ImageDraw.Draw(im);y=c['y'];rows=[]
 for j,fmt in enumerate(c['lignes']):
  value=fmt.format_map(rep);n=T['secondaire_px'] if j else T['taille_px'];f=font(n)
  while n>20 and (len(wrap(value,f))>4 or max(f.getlength(l) for l in wrap(value,f))>T['largeur']):n-=1;f=font(n)
  for line in wrap(value,f):
   # Subtle shadow, never a box or a thick outline.
   d.text((W//2,y+2),line,font=f,fill=(16,11,18,135),anchor='mt',stroke_width=1,stroke_fill=(24,19,26,80));d.text((W//2,y),line,font=f,fill=T['couleur'],anchor='mt');rows.append(line);y+=int(n*1.25)
 box=im.getbbox();assert box and box[0]>=15 and box[2]<=W-15 and box[3]<Y-50;arr=np.array(im.crop(box));return box,arr[:,:,2::-1].copy(),arr[:,:,3:4].astype(np.float32)/255,rows

def crop(frame,w,h,z,cx=.5,cy=.5):
 ih,iw=frame.shape[:2];cw=min(iw,ih*w/h)/z;ch=cw*h/w;l=int(np.clip(cx*iw-cw/2,0,iw-cw));t=int(np.clip(cy*ih-ch/2,0,ih-ch));return cv.resize(frame[t:t+round(ch),l:l+round(cw)],(w,h),interpolation=cv.INTER_LINEAR)

def main(jobdir,out,credit):
 j=J(jobdir/'job.json');q=J(e['questions']);g=J(e['cartes']);assert j['version']==e['version']==plan['version'] and j['template_id']==e['template_id']==plan['template_id'];fields={v['cle']:v for v in q};rep=j['reponses'];assert set(rep)==set(fields) and all(isinstance(v,str) and v.strip() for k,v in rep.items());assert j['ecrans']==[v['numero'] for v in g]==list(range(1,13));caps=j['captures'];assert [c['scene'] for c in caps]==[s['id'] for s in scenes] and len({c['sha256'] for c in caps})==4;assert H(T['fonte'])==T['sha256'];out.mkdir(exist_ok=True,parents=True);over=[overlay(c,rep) for c in T['fenetres']];proof=[{**c,'affiche':o[3],'bounds':o[0]} for c,o in zip(T['fenetres'],over)];assert all(c['debut']==(0 if i==0 else T['fenetres'][i-1]['fin']) for i,c in enumerate(T['fenetres']));effects=plan['effets'];cuts={c['image']:c['zoom'] for c in effects['coupes']};style=1;dest=out/'T5-Un-client-raconte-01.mp4';enc=sp.Popen([F,'-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-r',str(FPS),'-s',f'{W}x{Y}','-i','-','-an','-c:v','libx264','-threads','3','-crf','18','-preset','veryfast','-pix_fmt','yuv420p','-metadata','comment='+credit,'-movflags','+faststart',str(dest)],stdin=sp.PIPE);samples=[]
 try:
  for sc,c in zip(scenes,caps):
   assert c['fichier']==sc['id']+'.video';p=jobdir/c['fichier'];assert H(p)==c['sha256'];cap=cv.VideoCapture(str(p));hz=cap.get(cv.CAP_PROP_FPS);assert hz>0;srcidx=-1
   for i in range(sc['debut'],sc['fin']):
    want=int((i-sc['debut'])*hz/FPS+1e-7)
    while srcidx<want:
     ok,frame=cap.read();assert ok,('Prise trop courte',sc['id'],i);srcidx+=1
    style=cuts.get(i,style);pic=crop(frame,W,Y,style);k=next(k for k,cue in enumerate(T['fenetres']) if cue['debut']<=i<cue['fin']);(x,y,r,b),color,alpha,_=over[k];cue=T['fenetres'][k];alpha=alpha*min(1,(i-cue['debut'])/T['entree_images'],(cue['fin']-1-i)/T['sortie_images']);sl=pic[y:b,x:r];sl[:]=color*alpha+sl*(1-alpha);enc.stdin.write(pic.tobytes());
    if i in (16,65,140,151,232,395,470,545,665,780,875,899):samples.append(cv.resize(pic,(180,320)))
   cap.release()
 finally:
  enc.stdin.close();stat=enc.wait()
 assert stat==0;cv.imwrite(str(out/'Planche.jpg'),np.vstack([np.hstack(samples[i:i+4]) for i in (0,4,8)]));(out/'preuve.json').write_text(json.dumps(dict(job=j,partition_sha256=H(e['partition']),mp4_sha256=H(dest),images=plan['images'],fenetres=proof,coupes=effects['coupes']),ensure_ascii=False,indent=2));(out/'CREDITS.txt').write_text(credit+'\n');return dest
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--job',type=P,required=True);ap.add_argument('--out',type=P,required=True);ap.add_argument('--demo',action='store_true');a=ap.parse_args();m=J('render/demo/plans.json');main(a.job,a.out,('Images : '+m['titre']+' — '+m['auteurs']+' — '+m['video']+' — Creative Commons Attribution. '+m['usage']) if a.demo else 'Images du job marchand.')
