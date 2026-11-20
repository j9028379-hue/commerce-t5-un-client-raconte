"""Finalisation conditionnelle : le journal distant, pas l’artefact, fait autorité."""
import base64, json, os, re, subprocess as sp, sys
from pathlib import Path

branch = 'state/commerce-autoplay'
endpoint = 'repos/'+os.environ['GITHUB_REPOSITORY']+'/contents/autoplay/etat.json'
gh = lambda *args: json.loads(sp.check_output(['gh','api',*args]))

def verifier(old, rows, result):
    if not isinstance(old,list) or not isinstance(rows,list): raise ValueError('Journal invalide')
    for seq in [old,rows]:
        if not all(isinstance(x,list) and len(x)==2 and isinstance(x[0],str) and re.fullmatch('[0-9a-f]{64}',x[0]) and type(x[1]) is int and 1<=x[1]<=4 for x in seq): raise ValueError('Livraison invalide')
        if len({x[0] for x in seq})!=len(seq) or any(a[1]==b[1] for a,b in zip(seq,seq[1:])): raise ValueError('Doublon ou répétition')
    item=[result['run_id'],result['music_id']]
    if result['status']!='COMPLETED' or result['template_id']!='COMMERCE-T5' or not re.fullmatch('[0-9a-f]{64}',result['sha256']):raise ValueError('Résultat non confirmé')
    if not (rows==old+[item] or (rows==old and item in old)): raise ValueError('Révision incohérente avec la livraison')

if __name__=='__main__':
    current=gh(endpoint+'?ref='+branch);remote=base64.b64decode(current['content']);etag=Path('work/etag')
    if sys.argv[1]=='lire':
        Path('work/etat.json').write_bytes(remote);etag.write_text(current['sha'])
    elif sys.argv[1] in ('confirmer','verifier'):
        new=Path('work/suivant.json').read_bytes();old=json.loads(remote);rows=json.loads(new)
        if current['sha']!=etag.read_text():raise ValueError('Journal déjà modifié')
        verifier(old,rows,json.loads(Path('work/RenderResult.json').read_text()))
        if sys.argv[1]=='confirmer' and rows!=old:gh('-X','PUT',endpoint,'-f','branch='+branch,'-f','sha='+current['sha'],'-f','message=Confirmer la livraison '+os.environ['GITHUB_RUN_ID'],'-f','content='+base64.b64encode(new).decode())
    else:raise ValueError('Action inconnue')
