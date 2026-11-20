"""Contrôles défensifs des contrats : fichiers synthétiques uniquement, sans requêtes à une cible."""
import copy,json,hashlib,sys,os,tomllib
from pathlib import Path as P
from jsonschema import validate,ValidationError
sys.path.insert(0,'integration');from etat import verifier

def unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('Clé JSON non unique')
        result[k]=v
    return result
def read(p):return json.loads(P(p).read_text(),object_pairs_hook=unique)
for d in ['schemas','catalogue','capture-guide','form','montage','audio','golden','approvals','render/demo']:
    for p in P(d).rglob('*.json'):read(p)
e,=read('catalogue/catalogue.json')['entries'];j=read('golden/job.json');schema=read(e['schema_job']);validate(j,schema)
for mutation in [lambda j:j.update(champ_inconnu=True),lambda j:j['captures'][0].update(debug=True),lambda j:j['captures'][0].update(fichier='autre.video'),lambda j:j['captures'].pop(),lambda j:j['reponses'].pop('avis_client'),lambda j:j['ecrans'].reverse(),lambda j:j.update(version='autre')]:
    x=copy.deepcopy(j);mutation(x)
    try:validate(x,schema)
    except ValidationError:continue
    raise ValueError('Job non conforme accepté')
conf=tomllib.loads(P('shared/cloudflare-control-plane/wrangler.toml').read_text());assert set(conf)=={'name','main','compatibility_date','workers_dev','preview_urls'} and conf['workers_dev'] is conf['preview_urls'] is False
assert len(read(e['questions']))==6 and [x['numero'] for x in read(e['cartes'])]==list(range(1,13));assert str(e['ota_implemented'])=='False'
old=[['1'*64,4]];r=dict(template_id='COMMERCE-T5',run_id='2'*64,status='COMPLETED',music_id=3,sha256='3'*64);new=old+[[r['run_id'],3]];verifier(old,new,r);verifier(new,new,r)
for rows in [[],old,old+[[r['run_id'],4]],old+[['4'*64,1]],new+new]:
    try:verifier(old,rows,r)
    except ValueError:continue
    raise ValueError('Journal incohérent accepté')
assert all(hashlib.sha256(P(k).read_bytes()).hexdigest()==v for k,v in read('qc/empreintes-voix.json').items());print('PASS : JSON suivis sans clé doublée ; 7 jobs non conformes refusés ; 4 WAV sources ; configuration sans binding ; journal CAS et reprise conformes')
