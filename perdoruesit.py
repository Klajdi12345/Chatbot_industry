"""Databaza e personave në Neo4j: profili (mosha, gjendjet, alergjitë) dhe historia e bisedave.

Struktura e grafit:
  (:Person {id, emer, mosha, shenime, krijuar, perditesuar})
  (:Person)-[:KA_GJENDJE]->(:Gjendje)                  <- nyjet ekzistuese (shtatzëni, ulçerë...)
  (:Person)-[:DERGOI]->(:Mesazh {id, roli, tekst, ora})
  (:Mesazh)-[:PER_SIMPTOMEN]->(:Simptome)
  (:Mesazh)-[:SUGJEROI]->(:Barna)

Kujdes: këto janë të dhëna shëndetësore (të ndjeshme). Ruaj vetëm me pëlqimin e personit
dhe fshiji kur personi e kërkon (fshi_person).
"""
import uuid

from config import query


def krijo_skemen():
    query("CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE")
    query("CREATE CONSTRAINT mesazh_id IF NOT EXISTS FOR (m:Mesazh) REQUIRE m.id IS UNIQUE")


def shto_person(emer: str, mosha: int | None = None, gjendjet: set[str] | None = None,
                shenime: str = "") -> str:
    pid = str(uuid.uuid4())
    query("CREATE (p:Person {id: $id, emer: $emer, mosha: $mosha, shenime: $shenime, "
          "krijuar: datetime(), perditesuar: datetime()})",
          id=pid, emer=emer.strip(), mosha=mosha, shenime=shenime.strip())
    vendos_gjendjet(pid, gjendjet or set())
    return pid


def perditeso_person(pid: str, emer: str | None = None, mosha: int | None = None,
                     gjendjet: set[str] | None = None, shenime: str | None = None):
    query("MATCH (p:Person {id: $id}) "
          "SET p.mosha = $mosha, p.perditesuar = datetime(), "
          "p.emer = coalesce($emer, p.emer), p.shenime = coalesce($shenime, p.shenime)",
          id=pid, emer=emer, mosha=mosha, shenime=shenime)
    if gjendjet is not None:
        vendos_gjendjet(pid, gjendjet)


def vendos_gjendjet(pid: str, gjendjet: set[str]):
    """Zëvendëson gjendjet e personit me listën e dhënë."""
    query("MATCH (p:Person {id: $id})-[r:KA_GJENDJE]->() DELETE r", id=pid)
    query("MATCH (p:Person {id: $id}) UNWIND $gj AS gid MATCH (g:Gjendje {id: gid}) "
          "MERGE (p)-[:KA_GJENDJE]->(g)", id=pid, gj=sorted(gjendjet))


def shto_gjendje(pid: str, gjendjet: set[str]):
    """Shton gjendje pa fshirë të vjetrat (p.sh. kur personi shkruan 'jam shtatzënë' në bisedë)."""
    if gjendjet:
        query("MATCH (p:Person {id: $id}) UNWIND $gj AS gid MATCH (g:Gjendje {id: gid}) "
              "MERGE (p)-[:KA_GJENDJE]->(g) SET p.perditesuar = datetime()", id=pid, gj=sorted(gjendjet))


def lista_personave() -> list[dict]:
    return query("MATCH (p:Person) RETURN p.id AS id, p.emer AS emer, p.mosha AS mosha "
                 "ORDER BY p.perditesuar DESC")


def merr_person(pid: str) -> dict | None:
    rows = query("MATCH (p:Person {id: $id}) OPTIONAL MATCH (p)-[:KA_GJENDJE]->(g:Gjendje) "
                 "RETURN p.id AS id, p.emer AS emer, p.mosha AS mosha, p.shenime AS shenime, "
                 "collect(g.id) AS gjendjet", id=pid)
    return rows[0] if rows else None


def fshi_person(pid: str):
    """Fshin personin bashkë me të gjitha mesazhet e tij."""
    query("MATCH (p:Person {id: $id}) OPTIONAL MATCH (p)-[:DERGOI]->(m:Mesazh) "
          "DETACH DELETE m, p", id=pid)


def ruaj_mesazh(pid: str, roli: str, tekst: str, simptomat: list[str] | None = None,
                barnat: list[str] | None = None):
    query("MATCH (p:Person {id: $pid}) "
          "CREATE (p)-[:DERGOI]->(m:Mesazh {id: $mid, roli: $roli, tekst: $tekst, ora: datetime()}) "
          "WITH m UNWIND (CASE WHEN size($simptomat) = 0 THEN [null] ELSE $simptomat END) AS sid "
          "OPTIONAL MATCH (s:Simptome {id: sid}) FOREACH (_ IN CASE WHEN s IS NULL THEN [] ELSE [1] END | "
          "  MERGE (m)-[:PER_SIMPTOMEN]->(s)) "
          "WITH DISTINCT m UNWIND (CASE WHEN size($barnat) = 0 THEN [null] ELSE $barnat END) AS bid "
          "OPTIONAL MATCH (b:Barna {id: bid}) FOREACH (_ IN CASE WHEN b IS NULL THEN [] ELSE [1] END | "
          "  MERGE (m)-[:SUGJEROI]->(b))",
          pid=pid, mid=str(uuid.uuid4()), roli=roli, tekst=tekst,
          simptomat=simptomat or [], barnat=barnat or [])


def historia(pid: str, limit: int = 50) -> list[dict]:
    rows = query("MATCH (:Person {id: $id})-[:DERGOI]->(m:Mesazh) "
                 "RETURN m.roli AS role, m.tekst AS content, toString(m.ora) AS ora "
                 "ORDER BY m.ora DESC LIMIT $limit", id=pid, limit=limit)
    return list(reversed(rows))


def simptomat_e_fundit(pid: str) -> list[str]:
    """Simptomat e mesazhit të fundit që kishte simptoma (për pyetjet vijuese)."""
    rows = query("MATCH (:Person {id: $id})-[:DERGOI]->(m:Mesazh)-[:PER_SIMPTOMEN]->(s:Simptome) "
                 "WITH m, collect(s.id) AS ids ORDER BY m.ora DESC LIMIT 1 RETURN ids", id=pid)
    return rows[0]["ids"] if rows else []


def barnat_e_fundit(pid: str) -> list[str]:
    """Ilaçet e sugjeruara në mesazhin e fundit që kishte ilaçe (për "sa herë ta marr?")."""
    rows = query("MATCH (:Person {id: $id})-[:DERGOI]->(m:Mesazh)-[r:SUGJEROI]->(b:Barna) "
                 "WITH m, collect(b.id) AS ids ORDER BY m.ora DESC LIMIT 1 RETURN ids", id=pid)
    return rows[0]["ids"] if rows else []


if __name__ == "__main__":
    krijo_skemen()
    print("Skema e personave u krijua.")
