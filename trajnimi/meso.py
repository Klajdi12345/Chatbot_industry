"""Mësimi i botit: i shton një simptome fraza ose fjalë kyçe, në data/njohurite.json dhe menjëherë në Neo4j.

    python -m trajnimi.meso "kam zënë të ftohtë" grip_ftohje      → shton frazën
    python -m trajnimi.meso --sinkronizo grip_ftohje kapsllek      → rifut simptomat nga JSON-i në graf

Çdo mësim regjistrohet te trajnimi/mesimet.json (kush, kur, çfarë), që të mund të rishikohet nga farmacisti.
Pas mësimit, nis vlerësimin (python -m trajnimi.vlereso) për të parë nëse saktësia u rrit.
"""
import argparse
import json
import threading
from datetime import datetime
from pathlib import Path

from config import ROOT, embed, normalizo, query
from gjuha import standardizo

NJOHURITE = ROOT / "data" / "njohurite.json"
REGJISTRI = Path(__file__).parent / "mesimet.json"
_bllok = threading.Lock()


def _lexo() -> dict:
    return json.loads(NJOHURITE.read_text(encoding="utf-8"))


def _shkruaj(d: dict):
    NJOHURITE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _regjistro(hyrja: dict):
    lista = json.loads(REGJISTRI.read_text(encoding="utf-8")) if REGJISTRI.exists() else []
    lista.append({"ora": datetime.now().strftime("%Y-%m-%d %H:%M"), **hyrja})
    REGJISTRI.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")


def _pastro_cache():
    try:
        import chatbot
        for f in ("_te_gjitha_barnat", "_numri_frazave"):
            getattr(chatbot, f).cache_clear()
    except Exception:  # noqa: BLE001
        pass


def sinkronizo(simptoma_ids: list[str]) -> dict:
    """Rifut në Neo4j fjalët kyçe dhe frazat (me embeddings) të këtyre simptomave nga JSON-i."""
    d = _lexo()
    S = {s["id"]: s for s in d["simptomat"]}
    rez = {}
    for sid in simptoma_ids:
        s = S[sid]
        query("MATCH (x:Simptome {id: $id}) SET x.fjale_kyce = $kw, x.emer = $emer, x.pershkrim = $p",
              id=sid, kw=s.get("fjale_kyce", ""), emer=s["emer"], p=s["pershkrim"])
        burimet = [s["emer"], s["pershkrim"], *s["fraza"]]
        tekste = sorted({normalizo(t) for t in burimet} | {standardizo(t) for t in burimet})
        vektoret = embed(tekste)
        query("MATCH (f:Fraze)-[:I_PERKET]->(:Simptome {id: $id}) DETACH DELETE f", id=sid)
        query("MATCH (s:Simptome {id: $id}) UNWIND $rows AS r CREATE (f:Fraze {tekst: r.tekst}) "
              "WITH s, f, r CALL db.create.setNodeVectorProperty(f, 'embedding', r.v) CREATE (f)-[:I_PERKET]->(s)",
              id=sid, rows=[{"tekst": t, "v": v} for t, v in zip(tekste, vektoret)])
        rez[sid] = len(tekste)
    _pastro_cache()
    return rez


def meso_fraze(fraza: str, simptoma_id: str, kush: str = "admin", burimi: str = "manual") -> dict:
    """I mëson botit që `fraza` do të thotë simptomën `simptoma_id`. Kthen {simptoma, fraza, e_re}."""
    fraza = " ".join((fraza or "").split())
    if not fraza or len(fraza) > 200:
        raise ValueError("Fraza duhet të ketë 1–200 karaktere.")
    with _bllok:
        d = _lexo()
        S = {s["id"]: s for s in d["simptomat"]}
        if simptoma_id not in S:
            raise ValueError(f"Simptomë e panjohur: {simptoma_id}")
        s = S[simptoma_id]
        e_re = normalizo(fraza) not in {normalizo(x) for x in s["fraza"]}
        if e_re:
            s["fraza"].append(fraza)
            _shkruaj(d)
            tekste = sorted({normalizo(fraza), standardizo(fraza)})
            query("MATCH (s:Simptome {id: $id}) UNWIND $rows AS r CREATE (f:Fraze {tekst: r.tekst}) "
                  "WITH s, f, r CALL db.create.setNodeVectorProperty(f, 'embedding', r.v) CREATE (f)-[:I_PERKET]->(s)",
                  id=simptoma_id, rows=[{"tekst": t, "v": v} for t, v in zip(tekste, embed(tekste))])
            _pastro_cache()
        _regjistro({"lloji": "fraze", "fraza": fraza, "simptoma": simptoma_id, "kush": kush, "burimi": burimi,
                    "e_re": e_re})
    return {"simptoma": s["emer"], "fraza": fraza, "e_re": e_re}


def lista_simptomave() -> list[dict]:
    return [{"id": s["id"], "emer": s["emer"]} for s in sorted(_lexo()["simptomat"], key=lambda s: s["emer"])]


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="Mësoji botit fraza të reja për simptomat.")
    a.add_argument("fraza", nargs="?", help="si e shkruajnë njerëzit, p.sh. \"kam zënë të ftohtë\"")
    a.add_argument("simptoma", nargs="?", help="id e simptomës, p.sh. grip_ftohje")
    a.add_argument("--sinkronizo", nargs="+", metavar="ID", help="rifut këto simptoma nga JSON-i në Neo4j")
    args = a.parse_args()
    if args.sinkronizo:
        print(sinkronizo(args.sinkronizo))
    elif args.fraza and args.simptoma:
        print(meso_fraze(args.fraza, args.simptoma, kush="terminali"))
    else:
        a.print_help()
