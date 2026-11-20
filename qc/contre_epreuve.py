import sys, subprocess as sp, json
from pathlib import Path as P

sys.path.insert(0, "render")
from marchand import run, J

if sys.argv[1] == "preparer":
    for i, (d, c) in enumerate(
        zip([6, 8, 7, 9], ["purple", "green", "maroon", "navy"]), 1
    ):
        cmd = [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={c}:s=360x640:r=30:d={d}",
        ]
        cmd += (
            ["-f", "lavfi", "-i", f"sine=frequency=280:duration={d}", "-c:a", "aac"]
            if i == 2
            else ["-an"]
        )
        sp.run(
            cmd + ["-c:v", "libx264", "-pix_fmt", "yuv420p", f"work/S{i}.mp4"],
            check=True,
        )
else:
    src = P("work/job")
    out = P("verification/marchand")
    db = P("verification/test.sqlite")
    r = run(src, out, db)
    assert r["status"] == "COMPLETED", r
    d = out / r["run_id"]
    assert J(d / "audio.json")["scenes_audio"] == ["S2"]
    j = J(d / "preuve.json")
    assert j["job"]["reponses"] == J("qc/marchand-test.json")
    txt=' '.join(' '.join(c['affiche']) for c in j['fenetres']);assert all(v in txt for v in J('qc/marchand-test.json').values())
    assert run(src, out, db) == r
    with (src / "S1.video").open("ab") as f:
        f.write(b"alteration")
    assert run(src, out, db)["status"] == "FAILED"
    print(
        "PASS : autre commerce, quatre prises, témoignage du marchand, son S2 seul, reprise et refus prise modifiée"
    )
