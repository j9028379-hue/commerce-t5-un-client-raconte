"""Prépare le cache éphémère du runner. Jamais de MP3 dans le ZIP, les logs ou les artefacts."""
import os,json,hashlib,subprocess as sp
from pathlib import Path as P
p=json.loads(P('audio/profil.json').read_text());count=0
for t in p['pistes']:
 i=t['numero'];url=os.getenv(f'T5_URL_{i}') if i!=4 else 'https://archive.org/download/royalty-free-music/Afrobeat%20Pop.mp3';sha=t['sha256'] or os.getenv(f'T5_SHA_{i}');
 if not url and not sha:continue
 if not url or not sha or not url.startswith('https://'):raise RuntimeError(f'Configuration incomplète : {i}')
 f=P('work')/f'musique-{i}.mp3';sp.run(['curl','--proto','=https','--proto-redir','=https','--retry','2','-fLs','--max-time','90',url,'-o',str(f)],check=False)
 if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=sha:raise RuntimeError(f'Média non vérifié : {i}')
 with open(os.environ['GITHUB_ENV'],'a') as out:out.write(f'T5_PRIVATE_{i:02}={f}\nT5_PRIVATE_{i:02}_SHA256={sha}\n');count+=1
if os.getenv('EXIGER_QUATRE')=='true' and count!=4:raise RuntimeError('Activation refusée : quatre originaux approuvés et contrôlés requis.')
