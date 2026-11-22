"""Backup i databazës Neo4j në Desktop dhe kopjim në një databazë lokale (Neo4j Desktop).

  python backup.py            → krijon Desktop\\FarmaBot_Backup\\<data_ora>\\ me:
                                 databaza.json   (të gjitha nyjet dhe lidhjet)
                                 databaza.cypher (skript që e rikrijon databazën kudo)
  python backup.py --lokal    → kopjon gjithë databazën Aura në Neo4j Desktop lokal
                                 (kërkon NEO4J_LOCAL_URI / _USERNAME / _PASSWORD te .env)
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from config import EMBED_DIM, query

DOSJA_BACKUP = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop" / "FarmaBot_Backup"
FUSHA_KOHE = {"krijuar", "perditesuar", "ora", "hyrja_fundit"}
SKEMA = [
    "CREATE CONSTRAINT barna_id IF NOT EXISTS FOR (n:Barna) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT simptome_id IF NOT EXISTS FOR (n:Simptome) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT gjendje_id IF NOT EXISTS FOR (n:Gjendje) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT mesazh_id IF NOT EXISTS FOR (m:Mesazh) REQUIRE m.id IS UNIQUE",
    "CREATE CONSTRAINT llogari_perdoruesi IF NOT EXISTS FOR (l:Llogari) REQUIRE l.perdoruesi IS UNIQUE",
    "CREATE CONSTRAINT llogari_email IF NOT EXISTS FOR (l:Llogari) REQUIRE l.email IS UNIQUE",
    "CREATE CONSTRAINT bisede_id IF NOT EXISTS FOR (b:Bisede) REQUIRE b.id IS UNIQUE",
    "CREATE CONSTRAINT reagim_id IF NOT EXISTS FOR (r:Reagim) REQUIRE r.id IS UNIQUE",
    "CREATE INDEX chunk_lloji IF NOT EXISTS FOR (c:Chunk) ON (c.lloji)",
    "CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS FOR (c:Chunk) ON c.embedding "
    "OPTIONS {indexConfig: {`vector.dimensions`: " + str(EMBED_DIM) + ", `vector.similarity_function`: 'cosine'}}",
    "CREATE VECTOR INDEX fraze_embedding IF NOT EXISTS FOR (f:Fraze) ON f.embedding "
    "OPTIONS {indexConfig: {`vector.dimensions`: " + str(EMBED_DIM) + ", `vector.similarity_function`: 'cosine'}}",
]


def _kohe_ne_tekst(v):
    return v.iso_format() if hasattr(v, "iso_format") else v


def eksporto() -> dict:
    """Lexon gjithë databazën. Kohët kthehen në tekst ISO (njësoj për Bolt dhe HTTPS)."""
    nyjet = query("MATCH (n) RETURN elementId(n) AS bid, labels(n) AS labels, properties(n) AS props")
    lidhjet = query("MATCH (a)-[r]->(b) RETURN elementId(a) AS nga, elementId(b) AS te, "
                    "type(r) AS tipi, properties(r) AS props")
    for x in nyjet + lidhjet:
        x["props"] = {k: _kohe_ne_tekst(v) for k, v in x["props"].items()}
    return {"krijuar": datetime.now().isoformat(timespec="seconds"), "nyjet": nyjet, "lidhjet": lidhjet}


# ---------------------------------------------------------------- skripti Cypher
def _literal(celesi: str, v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, list):
        return "[" + ", ".join(_literal("", x) for x in v) + "]"
    s = json.dumps(str(v), ensure_ascii=False)[1:-1].replace("'", "\\'")
    return f"datetime('{s}')" if celesi in FUSHA_KOHE else f"'{s}'"


def _harta(props: dict) -> str:
    return "{" + ", ".join(f"`{k}`: {_literal(k, v)}" for k, v in props.items()) + "}"


def ne_cypher(data: dict) -> str:
    rreshta = [f"// FarmaBot: backup i databazës Neo4j, {data['krijuar']}",
               "// Hape në Neo4j Browser / Neo4j Desktop (Query) ose: cypher-shell -f databaza.cypher",
               "// KUJDES: fshin të dhënat ekzistuese të databazës ku ekzekutohet.",
               "MATCH (n) DETACH DELETE n;"]
    rreshta += [s + ";" for s in SKEMA]
    rreshta.append("CREATE INDEX import_bid IF NOT EXISTS FOR (n:_Import) ON (n._bid);")
    for n in data["nyjet"]:
        etiketat = ":".join(f"`{l}`" for l in n["labels"]) + ":_Import"
        rreshta.append(f"CREATE (:{etiketat} {_harta({**n['props'], '_bid': n['bid']})});")
    for r in data["lidhjet"]:
        props = f" {_harta(r['props'])}" if r["props"] else ""
        rreshta.append(f"MATCH (a:_Import {{_bid: {_literal('', r['nga'])}}}), "
                       f"(b:_Import {{_bid: {_literal('', r['te'])}}}) "
                       f"CREATE (a)-[:`{r['tipi']}`{props}]->(b);")
    rreshta += ["MATCH (n:_Import) REMOVE n:_Import, n._bid;", "DROP INDEX import_bid IF EXISTS;"]
    return "\n".join(rreshta) + "\n"


def ruaj_backup() -> Path:
    data = eksporto()
    dosja = DOSJA_BACKUP / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dosja.mkdir(parents=True, exist_ok=True)
    (dosja / "databaza.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (dosja / "databaza.cypher").write_text(ne_cypher(data), encoding="utf-8")
    (dosja / "LEXOMË.txt").write_text(
        "Backup i FarmaBot-it nga databaza Neo4j.\n\n"
        f"Nyje: {len(data['nyjet'])}   Lidhje: {len(data['lidhjet'])}\n\n"
        "Për ta hapur në Neo4j Desktop:\n"
        "1. Neo4j Desktop → krijo një instancë lokale (Local instance) dhe nise.\n"
        "2. Hap Query, ngjit përmbajtjen e databaza.cypher dhe ekzekutoje\n"
        "   (ose: cypher-shell -u neo4j -p <fjalekalimi> -f databaza.cypher).\n\n"
        "KUJDES: përmban të dhëna shëndetësore të personave dhe hash-et e fjalëkalimeve. Mbaje të sigurt.\n",
        encoding="utf-8")
    return dosja


# ---------------------------------------------------------------- kopjim në Neo4j Desktop lokal
def ka_lokal() -> bool:
    return bool(os.getenv("NEO4J_LOCAL_URI"))


def kopjo_ne_lokal() -> dict:
    """Zëvendëson përmbajtjen e databazës lokale me një kopje të Aura-s."""
    from neo4j import GraphDatabase
    data = eksporto()
    uri = os.getenv("NEO4J_LOCAL_URI")
    if not uri:
        raise RuntimeError("Vendos NEO4J_LOCAL_URI, NEO4J_LOCAL_USERNAME, NEO4J_LOCAL_PASSWORD te .env")
    auth = (os.getenv("NEO4J_LOCAL_USERNAME", "neo4j"), os.getenv("NEO4J_LOCAL_PASSWORD"))
    db = os.getenv("NEO4J_LOCAL_DATABASE") or None
    with GraphDatabase.driver(uri, auth=auth) as d:
        d.verify_connectivity()
        ekz = lambda c, **p: d.execute_query(c, p, database_=db)
        ekz("MATCH (n) DETACH DELETE n")
        for s in SKEMA:
            ekz(s)
        ekz("CREATE INDEX import_bid IF NOT EXISTS FOR (n:_Import) ON (n._bid)")
        grupet: dict[tuple, list] = {}
        for n in data["nyjet"]:
            grupet.setdefault(tuple(n["labels"]), []).append(n)
        for labels, nyjet in grupet.items():
            etiketat = ":".join(f"`{l}`" for l in labels) + ":_Import"
            for i in range(0, len(nyjet), 200):
                rows = [{"bid": n["bid"], "props": {k: v for k, v in n["props"].items() if k not in FUSHA_KOHE},
                         "kohe": {k: v for k, v in n["props"].items() if k in FUSHA_KOHE and v}}
                        for n in nyjet[i:i + 200]]
                vendos_kohet = ", ".join(
                    f"x.{k} = CASE WHEN r.kohe.{k} IS NULL THEN null ELSE datetime(r.kohe.{k}) END"
                    for k in sorted(FUSHA_KOHE))
                ekz(f"UNWIND $rows AS r CREATE (x:{etiketat}) SET x = r.props, x._bid = r.bid, {vendos_kohet}",
                    rows=rows)
        tipet: dict[str, list] = {}
        for r in data["lidhjet"]:
            tipet.setdefault(r["tipi"], []).append(r)
        for tipi, lidhjet in tipet.items():
            for i in range(0, len(lidhjet), 500):
                ekz(f"UNWIND $rows AS r MATCH (a:_Import {{_bid: r.nga}}), (b:_Import {{_bid: r.te}}) "
                    f"CREATE (a)-[x:`{tipi}`]->(b) SET x = r.props", rows=lidhjet[i:i + 500])
        ekz("MATCH (n:_Import) REMOVE n:_Import, n._bid")
        ekz("DROP INDEX import_bid IF EXISTS")
    return {"nyje": len(data["nyjet"]), "lidhje": len(data["lidhjet"])}


if __name__ == "__main__":
    if "--lokal" in sys.argv:
        print("U kopjua në Neo4j lokal:", kopjo_ne_lokal())
    else:
        print("Backup-i u ruajt te:", ruaj_backup())
