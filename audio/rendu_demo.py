from mixer import marchand,H,I
from pathlib import Path as P
import json
v=P('work/master.mp4');m=P('work/piste.mp3');n=P('render/demo/voix/T5-Voix-seule.wav');out=P('livraison');out.mkdir(exist_ok=True);dest=out/'T5-Un-client-raconte-Afrobeat-Pop.mp4'
assert H(v)=='9fc089bd738706ae6aa12cd193ec1363ada4c953a9f12683239cc3463d593cdc' and H(m)=='690b333f6f4ff353e07e89467cd9c59e2c0d6d8284e4466e3b7e009940866326' and H(n)=='bf62ba635876220465676c3ab12ce347d60fd24f48179b6dc19a34015e66f283'
track=next(x for x in I('audio/selection.json')['pistes'] if x['id_pixabay']==151755);credit='Images : LED Noodle Lantern, Ruiz Brothers / Adafruit Industries (CC Attribution), https://www.youtube.com/watch?v=9Mak8Uz3F8c ; recadrées, ralenties et remontées. Musique : Afrobeat Pop — Nver Avetyan ; https://pixabay.com/music/afrobeat-afrobeat-pop-151755/ ; source audio : https://archive.org/details/royalty-free-music . Voix synthétique, témoignage de démonstration.'
cfg=dict(entree_musique_s=.38,mix=dict(lufs=-16,fond_db=-3,sous_parole_db=-10,attaque_ms=120,relachement_ms=450,ecart_min_db=8));proof=marchand(v,[],I('montage/partition.json')['scenes'],cfg,m,credit,dest,narration=n);(out/'controle.json').write_text(json.dumps(dict(**proof,musique=track,master_sha256=H(v),voix_sha256=H(n),film_sha256=H(dest)),ensure_ascii=False,indent=2));(out/'CREDITS.txt').write_text(credit+'\n');print(proof)
