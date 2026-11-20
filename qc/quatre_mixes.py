from pathlib import Path as P
import sys,json
sys.path.insert(0,'audio');from mixer import marchand,I,H
p=I('audio/profil.json');scenes=I('montage/partition.json')['scenes'];out=P('verification/mix');out.mkdir(parents=True,exist_ok=True);r=[]
for t in p['pistes']:
 f=P(t['fichier']);assert H(f)==t['sha256'] and t['redistribution_mp3'];dest=out/(f.stem+'.mp4');m=marchand('work/master.mp4',[],scenes,p,f,'Images : LED Noodle Lantern — Ruiz Brothers / Adafruit Industries (CC Attribution) https://www.youtube.com/watch?v=9Mak8Uz3F8c ; recadrées et remontées. Musique : '+t['credit'],dest,narration=p['voix_demo']);assert m['scenes_audio']==['S1','S2','S3','S4'] and m['image_inchangee'];r.append(dict(numero=t['numero'],titre=t['titre'],sha256=H(dest),**m))
assert len(r)==4;data=json.dumps(r,indent=2,ensure_ascii=False);(out/'controle-4-mixes.json').write_text(data);P('livraison/balance.json').write_text(data);print(data)
