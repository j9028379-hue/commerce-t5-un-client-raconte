"""Structure d’export identique ; empreintes des conteneurs vérifiées sur les prises de ce runner.
La fidélité visuelle est testée séparément sur les 900 images, jamais sur le nom d’un fichier.
"""
import hashlib,json
from pathlib import Path as P
from jsonschema import validate
J=lambda p:json.loads(P(p).read_text());j=J('work/job/job.json');g=J('golden/job.json');validate(j,J('schemas/render-job.json'))
for actual,reference in zip(j['captures'],g['captures']):
 assert actual['sha256']==hashlib.sha256((P('work/job')/actual['fichier']).read_bytes()).hexdigest();print(actual['scene'],actual['sha256'],reference['sha256']);actual.pop('sha256');reference.pop('sha256')
assert j==g,(j,g)
