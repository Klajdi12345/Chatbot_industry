"""Ngarkon bazën e njohurive (data/njohurite.json) në Neo4j si graf.

Struktura e grafit:
  (:Simptome)-[:TRAJTOHET_ME {rendi}]->(:Barna)
  (:Barna)-[:KUNDERINDIKOHET_PER {arsye}]->(:Gjendje)
  (:Barna)-[:KUJDES_ME {arsye}]->(:Gjendje)
  (:Fraze {tekst, embedding})-[:I_PERKET]->(:Simptome)   <- për kërkimin me vektorë

Ekzekuto:  python ngarko_grafin.py
"""
import json

from config import EMBED_DIM, INDEKSI_FRAZAVE, ROOT, embed, kontrollo_lidhjen, normalizo, query
from gjuha import standardizo


def krijo_skemen():
    for label in ("Barna", "Simptome", "Gjendje"):
        query(f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS "
              f"FOR (n:{label}) REQUIRE n.id IS UNIQUE")
    query(
        f"CREATE VECTOR INDEX {INDEKSI_FRAZAVE} IF NOT EXISTS "
        "FOR (f:Fraze) ON f.embedding "
        "OPTIONS {indexConfig: {`vector.dimensions`: " + str(EMBED_DIM) + ", "
        "`vector.similarity_function`: 'cosine'}}",

    )


def ngarko(data: dict):
    query("UNWIND $rows AS r MERGE (g:Gjendje {id: r.id}) SET g.emer = r.emer",
          rows=data["gjendjet"])

    for b in data["barnat"]:
        props = {k: v for k, v in b.items() if k not in ("kunderindikime", "kujdes")}
        query("MERGE (b:Barna {id: $id}) SET b = $props", id=b["id"], props=props)
        # Fshi lidhjet e vjetra që ndryshimet në JSON të reflektohen.
        query("MATCH (b:Barna {id: $id})-[r:KUNDERINDIKOHET_PER|KUJDES_ME]->() DELETE r",
              id=b["id"])
        for tip, celesi in (("KUNDERINDIKOHET_PER", "kunderindikime"), ("KUJDES_ME", "kujdes")):
            rows = [{"g": g, "arsye": a} for g, a in b.get(celesi, {}).items()]
            query(f"MATCH (b:Barna {{id: $id}}) UNWIND $rows AS r "
                  f"MATCH (g:Gjendje {{id: r.g}}) MERGE (b)-[x:{tip}]->(g) SET x.arsye = r.arsye",
                  id=b["id"], rows=rows)

    query("MATCH (f:Fraze) DETACH DELETE f")
    for s in data["simptomat"]:
        query("MERGE (s:Simptome {id: $id}) SET s.emer = $emer, s.pershkrim = $pershkrim, "
              "s.shenja_alarmi = $alarm, s.keshilla = $keshilla, s.fjale_kyce = $kw, "
              "s.info = $info, s.kerkon_mjek = $mjek",
              id=s["id"], emer=s["emer"], pershkrim=s["pershkrim"],
              alarm=s["shenja_alarmi"], keshilla=s.get("keshilla", []), kw=s.get("fjale_kyce", ""),
              info=s.get("info", ""), mjek=bool(s.get("kerkon_mjek")))
        query("MATCH (s:Simptome {id: $id})-[r:TRAJTOHET_ME]->() DELETE r", id=s["id"])
        query("MATCH (s:Simptome {id: $id}) UNWIND range(0, size($barnat)-1) AS i "
              "MATCH (b:Barna {id: $barnat[i]}) MERGE (s)-[r:TRAJTOHET_ME]->(b) SET r.rendi = i",
              id=s["id"], barnat=s["barnat"])

        # Çdo frazë ruhet si është (e normalizuar) dhe në shqip standard (gjuha.py), si edhe mesazhet.
        burimet = [s["emer"], s["pershkrim"], *s["fraza"]]
        tekste = sorted({normalizo(t) for t in burimet} | {standardizo(t) for t in burimet})
        vektoret = embed(tekste)
        query("MATCH (s:Simptome {id: $id}) UNWIND $rows AS r "
              "CREATE (f:Fraze {tekst: r.tekst}) "
              "WITH s, f, r CALL db.create.setNodeVectorProperty(f, 'embedding', r.v) "
              "CREATE (f)-[:I_PERKET]->(s)",
              id=s["id"], rows=[{"tekst": t, "v": v} for t, v in zip(tekste, vektoret)])
        print(f"  ✓ {s['emer']} ({len(tekste)} fraza)")


def main():
    data = json.loads((ROOT / "data" / "njohurite.json").read_text(encoding="utf-8"))
    print("Lidhja me Neo4j...")
    kontrollo_lidhjen()
    krijo_skemen()
    print("Po ngarkoj njohuritë (embeddings me bge-m3)...")
    ngarko(data)
    n = query("MATCH (b:Barna) WITH count(b) AS b MATCH (s:Simptome) "
              "RETURN b, count(s) AS s")[0]
    print(f"Gati: {n['b']} barna, {n['s']} simptoma në graf.")


if __name__ == "__main__":
    main()
