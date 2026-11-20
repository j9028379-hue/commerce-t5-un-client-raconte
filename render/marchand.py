"""Rendu complet, en mode marchand par défaut. Cache audio privé facultatif, aucune diffusion de sources privées."""

import os, sys, hashlib, json, tempfile, subprocess as sp, argparse
from pathlib import Path as P
from jsonschema import validate
from film import main as montage, J, H, plan, scenes, e

sys.path.insert(0, str(P(__file__).resolve().parents[1] / "audio"))
from mixer import marchand
from rotation import livrer


def dump(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")


def assets(a):
    out = {}
    for t in a["pistes"]:
        i = t["numero"]
        path = os.getenv(f'T5_PRIVATE_{i:02}')
        digest = t['sha256'] or os.getenv(f'T5_PRIVATE_{i:02}_SHA256')
        if path:
            p=P(path)
            if not p.is_file() or not digest or H(p)!=digest: raise ValueError(f'Média {i} invalide')
            out[i]=(p,t)
    if len({H(p) for p,t in out.values()})!=len(out): raise ValueError('Source dupliquée')
    return out


def run(src, dest, db, demo=False, delivery=""):
    dest.mkdir(exist_ok=True, parents=True)
    db.parent.mkdir(exist_ok=True, parents=True)
    stage = "JOB"
    try:
        def unique(items):
            d={}
            for k,v in items:
                if k in d: raise ValueError('Clé JSON dupliquée')
                d[k]=v
            return d
        j=json.loads((src/'job.json').read_text(),object_pairs_hook=unique)
        validate(j, J(e["schema_job"]))
        clips = [src / c["fichier"] for c in j["captures"]]
        assert len({H(p) for p in clips}) == 4 and all(
            H(p) == c["sha256"] for p, c in zip(clips, j["captures"])
        )
        a = J(e["audio"])
        assert a["voix_complete_validee"] and a["selection_musicale_validee"]
        assert a["id"] == plan["audio_profile"] == e["audio_profile"]
        voice = None
        if demo:
            assert j["reponses"] == J("render/demo/reponses.json")
            voice = P(a["voix_demo"])
            assert H(voice) == J(e["validation"])["voix_sha256"]
        jid = hashlib.sha256(
            json.dumps([j, demo, delivery], sort_keys=True).encode()
        ).hexdigest()
        final = dest / jid
        stage = "AUDIO"
        pool = assets(a)

        def produire(i):
            nonlocal stage
            if final.exists():
                rr = J(final / "RenderResult.json")
                validate(rr, J("schemas/render-result.json"))
                assert rr["music_id"] == i and H(final / rr["output"]) == rr["sha256"]
                return rr
            music, t = pool[i]
            stage = "MONTAGE"
            with tempfile.TemporaryDirectory(dir=dest) as tmp:
                w = P(tmp) / "sortie"
                credit = "Images du job marchand."
                if demo:
                    m = J("render/demo/plans.json")
                    credit = f"Images : {m['titre']} — {m['auteurs']} — {m['video']} — Creative Commons Attribution. {m['usage']}"
                master = montage(src, w, credit)
                stage = "AUDIO"
                credit += (
                    " Musique : "
                    + t.get(
                        "credit",
                        t["titre"] + " — " + t["source"] + " — " + t["licence"],
                    )
                    + " · extrait mixé, atténuation sous la parole."
                )
                rep = marchand(
                    master, clips, scenes, dict(a,entree_musique_s=t["entree_musique_s"]), music, credit, w / "Film.mp4", voice
                )
                dump(
                    w / "audio.json",
                    {
                        **rep,
                        "musique": t["titre"],
                        "eligibles": sorted(pool),
                        "voix": "démo validée" if demo else "prises du marchand",
                    },
                )
                (w / "CREDITS.txt").write_text(credit)
                streams = json.loads(
                    sp.check_output(
                        [
                            "ffprobe",
                            "-v",
                            "error",
                            "-count_frames",
                            "-show_streams",
                            "-of",
                            "json",
                            str(w / "Film.mp4"),
                        ]
                    )
                )["streams"]
                v, au = streams
                assert (
                    v["nb_read_frames"],
                    v["width"],
                    v["height"],
                    float(v["duration"]),
                    au["codec_name"],
                    au["channels"],
                ) == ("900", 720, 1280, 30, "aac", 2)
                rr = dict(
                    status="COMPLETED",
                    template_id=e["template_id"],
                    run_id=jid,
                    music_id=i,
                    output="Film.mp4",
                    sha256=H(w / "Film.mp4"),
                )
                validate(rr, J("schemas/render-result.json"))
                dump(w / "RenderResult.json", rr)
                os.replace(w, final)
                return rr

        return livrer(db, jid, pool, produire)
    except Exception as exc:
        err = dict(
            status="FAILED", stage=stage, message=str(exc)[:500] or "Contrôle refusé"
        )
        validate(err, J("schemas/render-error.json"))
        with tempfile.NamedTemporaryFile(
            mode="w", dir=dest, prefix="RenderError-", suffix=".json", delete=False
        ) as f:
            json.dump(err, f, ensure_ascii=False)
        return err


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    [ap.add_argument("--" + k, type=P, required=True) for k in ("job", "out", "state")]
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--delivery", default="")
    o = ap.parse_args()
    r = run(o.job, o.out, o.state, o.demo, o.delivery)
    print(json.dumps(r))
    sys.exit(r["status"] != "COMPLETED")
