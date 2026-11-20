from pathlib import Path as P, PurePosixPath
import json, sys, zipfile, hashlib, subprocess
from jsonschema import validate

H = lambda x: hashlib.sha256(x).hexdigest()
base = P(__file__).resolve().parents[1]
J = lambda p: json.loads((base / p).read_text())


def verify(z):
    with zipfile.ZipFile(z) as f:
        m = json.loads(f.read("MANIFEST.json"))
        validate(m, J("schemas/package.json"))
        rows = m["files"]
        names = f.namelist()
        expected = {r["path"] for r in rows}
        assert (
            len(names) == len(set(names))
            and len(expected) == len(rows)
            and set(names) == expected | {"MANIFEST.json"}
        )
        for r in rows:
            n = r["path"]
            assert (
                not PurePosixPath(n).is_absolute()
                and ".." not in PurePosixPath(n).parts
                and "\\" not in n
            )
            b = f.read(n)
            assert (len(b), H(b)) == (r["bytes"], r["sha256"])
        assert {
            "catalogue/catalogue.json",
            "audio/CREDITS.md",
            "docs/assets/OFL.txt",
            "render/marchand.py",
        } <= expected
        entry = json.loads(f.read("catalogue/catalogue.json"))["entries"][0]
        audio = json.loads(f.read(entry["audio"]))
        assert all(
            H(f.read(t["fichier"])) == t["sha256"]
            for t in audio["pistes"]
            if t["redistribution_mp3"]
        )
        assert len(audio["pistes"]) == 4 and {
            n for n in expected if n.lower().endswith(".mp3")
        } == {t["fichier"] for t in audio["pistes"] if t["redistribution_mp3"]}
        for k in ["partition", "questions", "cartes", "schema_job", "validation"]:
            assert entry[k] in expected
        return m


if __name__ == "__main__":
    z = P(sys.argv[-1])
    if sys.argv[1] == "verify":
        print(len(verify(z)["files"]))
        sys.exit()
    rows = []
    entry = J("catalogue/catalogue.json")["entries"][0]
    names = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=base)
        .decode()
        .split("\0")
    )
    z.parent.mkdir(exist_ok=True, parents=True)
    with zipfile.ZipFile(z, "w", compression=zipfile.ZIP_DEFLATED) as f:
        for n in sorted(filter(None, names)):
            b = (base / n).read_bytes()
            f.writestr(n, b)
            rows.append(dict(path=n, role=n.split("/")[0], bytes=len(b), sha256=H(b)))
        f.writestr(
            "MANIFEST.json",
            json.dumps(
                dict(
                    template_id=entry["template_id"],
                    version=entry["version"],
                    schema_version="1.0.0",
                    commit=subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], cwd=base, text=True
                    ).strip(),
                    files=rows,
                )
            ),
        )
    verify(z)
