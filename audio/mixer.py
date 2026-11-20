"""Utilitaires PCM du moteur T1/T2 ; pas de téléchargement de musique."""

from pathlib import Path as P
import sys, os, re, json, hashlib, tempfile, subprocess, math
import numpy as np

D = P(__file__).resolve().parent
R = 48000
F = os.environ.get("FFMPEG", "ffmpeg")
H = lambda p: hashlib.sha256(P(p).read_bytes()).hexdigest()
I = lambda p: json.loads(P(p).read_text())
run = lambda a, **kw: subprocess.run(a, check=True, **kw)


def decode(p):
    return np.frombuffer(
        subprocess.check_output(
            [
                F,
                "-v",
                "error",
                "-i",
                str(p),
                "-map",
                "0:a:0",
                "-ar",
                str(R),
                "-ac",
                "2",
                "-f",
                "f32le",
                "-",
            ]
        ),
        "<f4",
    ).reshape(-1, 2)


def level(x):
    s = run(
        [
            F,
            "-hide_banner",
            "-nostats",
            "-f",
            "f32le",
            "-ar",
            str(R),
            "-ac",
            "2",
            "-i",
            "-",
            "-af",
            "loudnorm=print_format=json",
            "-f",
            "null",
            "-",
        ],
        input=np.asarray(x, "<f4").tobytes(),
        capture_output=True,
    ).stderr.decode()
    j = json.loads(re.findall(r"\{[^{}]+\}", s)[-1])
    return float(j["input_i"]), float(j["input_tp"])


def db(x):
    return 10 ** (x / 20)


def vh(p):
    return (
        subprocess.check_output(
            [
                F,
                "-v",
                "error",
                "-i",
                str(p),
                "-map",
                "0:v",
                "-c",
                "copy",
                "-f",
                "hash",
                "-hash",
                "sha256",
                "-",
            ]
        )
        .decode()
        .strip()
    )


def marchand(master, clips, scenes, profile, music, credit, target, narration=None):
    cfg = profile["mix"]
    v = np.zeros((30 * R, 2), np.float32)
    audibles = []
    if narration is not None:
        v = decode(narration).copy()
        assert v.shape == (30 * R, 2)
        audibles = [s["id"] for s in scenes]
    for p, sc in zip([] if narration else clips, scenes):
        present = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=index",
                "-of",
                "csv=p=0",
                str(p),
            ]
        ).strip()
        if present:
            start, end = (sc[key] * R // 30 for key in ("debut", "fin"))
            a = decode(p)[: end - start]
            v[start : start + len(a)] = a
            if len(a) and abs(a).max() > 0.005:
                audibles.append(sc["id"])
    if audibles:
        li, tp = level(v)
        v *= db(min(-18.7 - li, -3 - tp))
    tt = np.arange(len(v)) / R
    env = np.zeros(len(v))
    active = np.sqrt((v.reshape(-1, 480, 2) ** 2).mean(axis=(1, 2))) > 0.005
    idx = np.flatnonzero(active)
    attack = cfg["attaque_ms"] / 1000
    release = cfg["relachement_ms"] / 1000
    for rg in np.split(idx, np.flatnonzero(np.diff(idx) > 48) + 1):
        if len(rg):
            env = np.maximum(
                env,
                np.minimum(
                    np.clip((tt - rg[0] / 100 + attack) / attack, 0, 1),
                    np.clip(((rg[-1] + 1) / 100 + release - tt) / release, 0, 1),
                ),
            )
    source = decode(music)
    n0 = int(profile.get('entree_musique_s', 0) * R)
    m = source[n0:n0+len(v)].copy()
    m[:240] *= np.linspace(0,1,240)[:,None]
    m[-36000:] *= np.linspace(1,0,36000)[:,None]
    assert m.shape == v.shape
    m *= db(-18 - level(m)[0])
    m *= db((cfg["fond_db"] + (cfg["sous_parole_db"] - cfg["fond_db"]) * env)[:, None])
    sel = np.repeat(active, 480)
    if np.any(sel):
        m *= db(
            min(
                0,
                10 * np.log10(np.mean(v[sel] ** 2) / max(1e-12, np.mean(m[sel] ** 2)))
                - cfg["ecart_min_db"],
            )
        )
    par_scene = {}
    for sc in scenes:
        sl = slice(sc['debut']*R//30, sc['fin']*R//30)
        mask = sel[sl]
        if np.any(mask):
            ratio = float(10*np.log10(np.mean(v[sl][mask]**2)/max(1e-12,np.mean(m[sl][mask]**2))))
            par_scene[sc['id']]=round(ratio,3)
            if ratio < 4: raise ValueError('Parole masquée, scène '+sc['id'])
    x = v + m
    x *= db(cfg["lufs"] - level(x)[0])
    x = np.clip(x, -db(-2.6), db(-2.6))
    run(
        [
            F,
            "-v",
            "error",
            "-y",
            "-i",
            str(master),
            "-f",
            "f32le",
            "-ar",
            str(R),
            "-ac",
            "2",
            "-i",
            "-",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-metadata",
            "comment=" + credit,
            "-movflags",
            "+faststart",
            str(target),
        ],
        input=np.asarray(x, "<f4").tobytes(),
    )
    a = decode(target)
    li, tp = level(a)
    assert (
        vh(master) == vh(target)
        and abs(len(a) / R - 30) < 0.04
        and abs(li - cfg["lufs"]) <= 0.5
        and tp <= -1
    ), (li, tp)
    gap = (
        float(10 * np.log10(np.mean(v[sel] ** 2) / max(1e-12, np.mean(m[sel] ** 2))))
        if np.any(sel)
        else None
    )
    assert gap is None or gap >= cfg["ecart_min_db"] - 0.01
    return dict(
        scenes_audio=audibles, ecart_par_scene_db=par_scene,
        lufs=li,
        true_peak_dbtp=tp,
        voix_sur_musique_db=gap,
        image_inchangee=True,
    )
