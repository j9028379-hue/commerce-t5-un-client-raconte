"""Une transaction par décision : même job = même piste ; seules les livraisons confirmées comptent."""

from pathlib import Path
from collections import Counter
import sqlite3, secrets, json


def choisir(disponibles, historique, rng=secrets.choice):
    dernier = historique[-1] if historique else None
    possibles = sorted(set(disponibles) - {dernier})
    counts = Counter(historique)
    if not possibles:
        raise ValueError("Pas de piste disponible différente de la dernière")
    faible = min(counts[i] for i in possibles)
    return rng([i for i in possibles if counts[i] == faible])


def connect(path):
    con = sqlite3.connect(path, timeout=600)
    con.execute(
        "CREATE TABLE IF NOT EXISTS deliveries(seq INTEGER PRIMARY KEY,job TEXT UNIQUE NOT NULL,track INTEGER NOT NULL CHECK(track between 1 and 4))"
    )
    return con


def livrer(path, job, disponibles, produire):
    con = connect(path)
    try:
        con.execute("BEGIN IMMEDIATE")
        old = con.execute("SELECT track FROM deliveries WHERE job=?", (job,)).fetchone()
        track = (
            old[0]
            if old
            else choisir(
                disponibles,
                [
                    r[0]
                    for r in con.execute("SELECT track FROM deliveries ORDER BY seq")
                ],
            )
        )
        result = produire(track)
        if not old:
            con.execute("INSERT INTO deliveries(job,track) VALUES (?,?)", (job, track))
        con.commit()
        return result
    finally:
        con.close()


def transfer(action, path, file):
    con = connect(path)
    with con:
        if action == "import":
            rows = json.loads(Path(file).read_text())
            assert not con.execute("select count(*) from deliveries").fetchone()[0]
            assert all(x[1] != y[1] for x, y in zip(rows, rows[1:]))
            con.executemany("insert into deliveries(job,track) values(?,?)", rows)
        else:
            Path(file).write_text(
                json.dumps(
                    con.execute(
                        "select job,track from deliveries order by seq"
                    ).fetchall(),
                    indent=2,
                )
                + "\n"
            )
    con.close()


if __name__ == "__main__":
    import sys

    transfer(*sys.argv[1:])
