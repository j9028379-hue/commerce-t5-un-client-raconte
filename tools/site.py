from pathlib import Path as P
import json
J=lambda p:json.loads(P(p).read_text());c=J('catalogue/catalogue.json')['entries'][0];P('docs/data.js').write_text('const T5='+json.dumps(dict(carte=c,questions=J(c['questions']),ecrans=J(c['cartes']),plan=J(c['partition'])),ensure_ascii=False)+';\n')
