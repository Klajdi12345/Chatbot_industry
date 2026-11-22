"""Bisedat e ruajtura (si lista e bisedave te ChatGPT / Claude).

  (:Person)-[:KA_BISEDE]->(:Bisede {id, titull, krijuar, perditesuar, konteksti})
  (:Bisede)-[:PERMBAN]->(:Mesazh {id, roli, tekst, ora, te_dhena})
  (:Person)-[:DERGOI]->(:Mesazh)                 <- si më parë (statistikat dhe historia e vjetër)

`konteksti` (JSON): simptomat, barnat, pyetja sqaruese në pritje, që biseda të vazhdojë kur rihapet.
`te_dhena` (JSON): kartat e ilaçeve, hapat e mendimit dhe burimet e përgjigjes, për t'i rishfaqur.
Mesazhet e vjetra pa bisedë mblidhen një herë në një bisedë "Biseda e mëparshme".
"""
import json
import uuid

from config import query


def krijo_skemen():
    query("CREATE CONSTRAINT bisede_id IF NOT EXISTS FOR (b:Bisede) REQUIRE b.id IS UNIQUE")


def _migro(pid: str):
    """Mesazhet e versionit të vjetër (pa bisedë) bashkohen në një bisedë."""
    rows = query("MATCH (p:Person {id: $pid})-[:DERGOI]->(m:Mesazh) WHERE NOT ()-[:PERMBAN]->(m) "
                 "RETURN count(m) AS n, min(m.ora) AS fillimi, max(m.ora) AS fundi", pid=pid)
    if not rows or not rows[0]["n"]:
        return
    query("MATCH (p:Person {id: $pid}) "
          "CREATE (p)-[:KA_BISEDE]->(b:Bisede {id: $bid, titull: 'Biseda e mëparshme', krijuar: $fillimi, "
          "perditesuar: $fundi, konteksti: '{}'}) WITH p, b "
          "MATCH (p)-[:DERGOI]->(m:Mesazh) WHERE NOT ()-[:PERMBAN]->(m) MERGE (b)-[:PERMBAN]->(m)",
          pid=pid, bid=str(uuid.uuid4()), fillimi=rows[0]["fillimi"], fundi=rows[0]["fundi"])


def lista(pid: str) -> list[dict]:
    _migro(pid)
    return query("MATCH (:Person {id: $pid})-[:KA_BISEDE]->(b:Bisede) "
                 "RETURN b.id AS id, b.titull AS titull, toString(b.perditesuar) AS perditesuar "
                 "ORDER BY b.perditesuar DESC", pid=pid)


def krijo(pid: str, titull: str) -> str:
    bid = str(uuid.uuid4())
    query("MATCH (p:Person {id: $pid}) CREATE (p)-[:KA_BISEDE]->(:Bisede {id: $bid, titull: $t, "
          "krijuar: datetime(), perditesuar: datetime(), konteksti: '{}'})", pid=pid, bid=bid, t=titull)
    return bid


def i_perket(pid: str, bid: str) -> bool:
    return bool(query("MATCH (:Person {id: $pid})-[:KA_BISEDE]->(b:Bisede {id: $bid}) RETURN 1 AS x",
                      pid=pid, bid=bid))


def mesazhet(bid: str) -> list[dict]:
    rows = query("MATCH (:Bisede {id: $bid})-[:PERMBAN]->(m:Mesazh) "
                 "RETURN m.roli AS role, m.tekst AS content, m.te_dhena AS te_dhena, toString(m.ora) AS ora "
                 "ORDER BY m.ora", bid=bid)
    for r in rows:
        r["te_dhena"] = json.loads(r["te_dhena"]) if r["te_dhena"] else None
    return rows


def ruaj_mesazh(pid: str, bid: str, roli: str, tekst: str, simptomat: list[str] | None = None,
                barnat: list[str] | None = None, te_dhena: dict | None = None):
    query("MATCH (p:Person {id: $pid})-[:KA_BISEDE]->(b:Bisede {id: $bid}) "
          "CREATE (p)-[:DERGOI]->(m:Mesazh {id: $mid, roli: $roli, tekst: $tekst, ora: datetime(), "
          "te_dhena: $te_dhena}), (b)-[:PERMBAN]->(m) SET b.perditesuar = datetime() "
          "WITH m UNWIND (CASE WHEN size($simptomat) = 0 THEN [null] ELSE $simptomat END) AS sid "
          "OPTIONAL MATCH (s:Simptome {id: sid}) FOREACH (_ IN CASE WHEN s IS NULL THEN [] ELSE [1] END | "
          "  MERGE (m)-[:PER_SIMPTOMEN]->(s)) "
          "WITH DISTINCT m UNWIND (CASE WHEN size($barnat) = 0 THEN [null] ELSE $barnat END) AS bid2 "
          "OPTIONAL MATCH (x:Barna {id: bid2}) FOREACH (_ IN CASE WHEN x IS NULL THEN [] ELSE [1] END | "
          "  MERGE (m)-[:SUGJEROI]->(x))",
          pid=pid, bid=bid, mid=str(uuid.uuid4()), roli=roli, tekst=tekst,
          te_dhena=json.dumps(te_dhena, ensure_ascii=False) if te_dhena else None,
          simptomat=simptomat or [], barnat=barnat or [])


def konteksti(bid: str) -> dict:
    rows = query("MATCH (b:Bisede {id: $bid}) RETURN b.konteksti AS k", bid=bid)
    return json.loads(rows[0]["k"] or "{}") if rows else {}


def ruaj_kontekstin(bid: str, k: dict):
    query("MATCH (b:Bisede {id: $bid}) SET b.konteksti = $k", bid=bid, k=json.dumps(k, ensure_ascii=False))


def riemerto(bid: str, titull: str):
    query("MATCH (b:Bisede {id: $bid}) SET b.titull = $t", bid=bid, t=titull)


def fshi(bid: str):
    """Fshin bisedën dhe mesazhet e saj."""
    query("MATCH (b:Bisede {id: $bid}) OPTIONAL MATCH (b)-[:PERMBAN]->(m:Mesazh) DETACH DELETE m, b", bid=bid)


def fshi_te_gjitha(pid: str):
    query("MATCH (:Person {id: $pid})-[:KA_BISEDE]->(b:Bisede) OPTIONAL MATCH (b)-[:PERMBAN]->(m:Mesazh) "
          "DETACH DELETE m, b", pid=pid)
