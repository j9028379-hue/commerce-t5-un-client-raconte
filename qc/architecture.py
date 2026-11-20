import json, tempfile, sys, random, zipfile, hashlib
from pathlib import Path as P
from concurrent.futures import ThreadPoolExecutor
from jsonschema import validate

sys.path[:0] = ["audio", "package"]
from rotation import choisir, livrer, connect
from livrer import verify

J = lambda p: json.loads(P(p).read_text())
e = J("catalogue/catalogue.json")["entries"][0]
a = J(e["audio"])
s = J(e["partition"])
validate(s, J("schemas/template.json"))
validate(J("golden/job.json"), J(e["schema_job"]))
assert all(
    a[k]
    for k in ("voix_complete_validee", "selection_commerciale_autorisee", "rotation_active")
)
assert (
    len(J(e["cartes"])) == 12
    and len(J(e["questions"])) == 6
    and e["version"] == s["version"] == a["version"]
)
assert (
    hashlib.sha256(P(a["voix_demo"]).read_bytes()).hexdigest()
    == J(e["validation"])["voix_sha256"]
)
for pool in ([1, 2, 3, 4], [1, 3, 4]):
    r = random.Random(42)
    h = []
    for i in range(10000):
        new = choisir(pool, h, r.choice)
        assert not h or new != h[-1]
        h.append(new)
    assert (
        set(h) == set(pool)
        and max(h.count(i) for i in pool) - min(h.count(i) for i in pool) <= 1
        and any(h[k] != h[k - len(pool)] for k in range(len(pool), len(h)))
    )
with tempfile.TemporaryDirectory() as tmp:
    db = P(tmp) / "test.sqlite"
    f = lambda i: i
    try:
        livrer(db, "erreur", [1, 3], lambda i: 1 / 0)
    except ZeroDivisionError:
        pass
    assert connect(db).execute("select count(*) from deliveries").fetchone()[0] == 0
    with ThreadPoolExecutor(4) as worker:
        old = list(worker.map(lambda _: livrer(db, "meme", [1, 3, 4], f), range(4)))
        assert len(set(old)) == 1
    assert livrer(db, "autre", [1, 3, 4], f) != old[0]
    assert connect(db).execute("select count(*) from deliveries").fetchone()[0] == 2
    if len(sys.argv) > 1:
        z = sys.argv[1]
        verify(z)
        bad = P(tmp) / "modifie.zip"
        with zipfile.ZipFile(z) as src, zipfile.ZipFile(bad, "w") as dst:
            for n in src.namelist():
                dst.writestr(n, src.read(n) + (b" " if n == e["partition"] else b""))
        try:
            verify(bad)
        except AssertionError:
            pass
        else:
            raise ValueError("Paquet altéré accepté")
print(
    "PASS : contrats, voix validée, rotation non cyclique, concurrence, reprise, échec sans avancement ; manifeste si fourni"
)
