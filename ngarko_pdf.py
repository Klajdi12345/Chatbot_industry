"""Ngarkon fletëudhëzues barnash (PDF) në Neo4j për kërkim me vektorë.

Vendos PDF-të në  data/pdf/  dhe ekzekuto:  python ngarko_pdf.py
Nëse emri i skedarit përmban id-në e një ilaçi (p.sh. 'ibuprofen_brufen.pdf'),
pjesët lidhen me nyjen (:Barna) përkatëse.
"""
import pymupdf

from config import EMBED_DIM, INDEKSI_PDF, ROOT, embed, kontrollo_lidhjen, normalizo, query


def ndaj_tekstin(tekst: str, madhesia: int = 900, mbivendosja: int = 150) -> list[str]:
    """Ndan tekstin në pjesë ~900 karaktere, duke u përpjekur të presë te paragrafët."""
    paragrafet = [p.strip() for p in tekst.split("\n\n") if p.strip()]
    pjeset, aktuale = [], ""
    for p in paragrafet:
        if len(aktuale) + len(p) + 1 <= madhesia:
            aktuale = f"{aktuale}\n{p}" if aktuale else p
            continue
        if aktuale:
            pjeset.append(aktuale)
        while len(p) > madhesia:
            pjeset.append(p[:madhesia])
            p = p[madhesia - mbivendosja:]
        aktuale = p
    if aktuale:
        pjeset.append(aktuale)
    return pjeset

DOSJA = ROOT / "data" / "pdf"


def main():
    DOSJA.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(DOSJA.glob("*.pdf"))
    if not pdfs:
        print(f"Nuk ka PDF në {DOSJA}. Vendos fletëudhëzuesit aty dhe provo përsëri.")
        return

    kontrollo_lidhjen()
    query(f"CREATE VECTOR INDEX {INDEKSI_PDF} IF NOT EXISTS FOR (c:Chunk) ON c.embedding "
          "OPTIONS {indexConfig: {`vector.dimensions`: " + str(EMBED_DIM) + ", "
          "`vector.similarity_function`: 'cosine'}}")
    id_barnash = [r["id"] for r in query("MATCH (b:Barna) RETURN b.id AS id")]
    for pdf in pdfs:
        with pymupdf.open(pdf) as doc:
            faqet = [(i + 1, f.get_text()) for i, f in enumerate(doc)]
        rows = []
        for faqja, tekst in faqet:
            for pjese in ndaj_tekstin(tekst):
                if len(pjese.strip()) > 40:
                    rows.append({"tekst": pjese.strip(), "faqja": faqja})
        if not rows:
            print(f"  ! {pdf.name}: nuk u gjet tekst (mund të jetë PDF i skanuar)")
            continue
        vektoret = embed([normalizo(r["tekst"]) for r in rows])
        for r, v in zip(rows, vektoret):
            r["v"] = v

        emri = normalizo(pdf.stem)
        barna = next((b for b in id_barnash if b in emri.replace(" ", "_")), None)
        query("MATCH (c:Chunk {burimi: $burimi}) DETACH DELETE c", burimi=pdf.name)
        query("UNWIND $rows AS r CREATE (c:Chunk {tekst: r.tekst, faqja: r.faqja, burimi: $burimi}) "
              "WITH c, r CALL db.create.setNodeVectorProperty(c, 'embedding', r.v) "
              "WITH c OPTIONAL MATCH (b:Barna {id: $barna}) "
              "FOREACH (_ IN CASE WHEN b IS NULL THEN [] ELSE [1] END | MERGE (c)-[:PERSHKRUAN]->(b))",
              rows=rows, burimi=pdf.name, barna=barna)
        print(f"  ✓ {pdf.name}: {len(rows)} pjesë" + (f" → {barna}" if barna else ""))


if __name__ == "__main__":
    main()
