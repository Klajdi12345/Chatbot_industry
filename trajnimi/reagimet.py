"""Reagimet e përdoruesve (👍 / 👎) për përgjigjet e botit, në Neo4j.

  (:Reagim {id, vlera (1 | -1), arsye, koment, pyetja, pergjigjja, simptomat, gjuha, perdoruesi,
            ora, statusi ("hapur" | "zgjidhur"), zgjidhja})

Admini i sheh te Paneli i administratorit → Trajnimi dhe ia mëson botit përgjigjen e saktë (trajnimi/meso.py).
"""
import uuid

from config import query

ARSYET = ("nuk_kuptoi", "ilac_gabim", "e_paqarte", "tjeter")


def krijo_skemen():
    query("CREATE CONSTRAINT reagim_id IF NOT EXISTS FOR (r:Reagim) REQUIRE r.id IS UNIQUE")


def ruaj(vlera: int, pyetja: str, pergjigjja: str, arsye: str = "", koment: str = "",
         simptomat: list[str] | None = None, gjuha: str = "sq", perdoruesi: str | None = None) -> str:
    if vlera not in (1, -1):
        raise ValueError("Vlerësimi duhet të jetë 1 ose -1.")
    rid = str(uuid.uuid4())
    query("CREATE (:Reagim {id: $id, vlera: $v, arsye: $a, koment: $k, pyetja: $p, pergjigjja: $pg, "
          "simptomat: $s, gjuha: $g, perdoruesi: $u, ora: localdatetime(), statusi: $st})",
          id=rid, v=vlera, a=arsye if arsye in ARSYET else "", k=(koment or "")[:1000],
          p=(pyetja or "")[:2000], pg=(pergjigjja or "")[:6000], s=simptomat or [], g=gjuha,
          u=perdoruesi, st="hapur" if vlera < 0 else "zgjidhur")
    return rid


def lista(vetem_te_hapura: bool = True, limit: int = 100) -> list[dict]:
    return query("MATCH (r:Reagim) WHERE r.vlera = -1 AND ($hapura = false OR r.statusi = 'hapur') "
                 "RETURN r.id AS id, r.arsye AS arsye, r.koment AS koment, r.pyetja AS pyetja, "
                 "r.pergjigjja AS pergjigjja, r.simptomat AS simptomat, r.gjuha AS gjuha, r.perdoruesi AS perdoruesi, "
                 "substring(toString(r.ora), 0, 16) AS ora, r.statusi AS statusi, r.zgjidhja AS zgjidhja "
                 "ORDER BY r.ora DESC LIMIT $limit", hapura=vetem_te_hapura, limit=limit)


def numrat() -> dict:
    r = query("MATCH (r:Reagim) RETURN sum(CASE WHEN r.vlera = 1 THEN 1 ELSE 0 END) AS pelqime, "
              "sum(CASE WHEN r.vlera = -1 THEN 1 ELSE 0 END) AS ankesa, "
              "sum(CASE WHEN r.vlera = -1 AND r.statusi = 'hapur' THEN 1 ELSE 0 END) AS te_hapura")
    return {k: v or 0 for k, v in r[0].items()} if r else {"pelqime": 0, "ankesa": 0, "te_hapura": 0}


def zgjidh(rid: str, zgjidhja: str = "") -> bool:
    return bool(query("MATCH (r:Reagim {id: $id}) SET r.statusi = 'zgjidhur', r.zgjidhja = $z RETURN r.id AS id",
                      id=rid, z=zgjidhja[:300]))
