"""Ngarkon datasetet e shkarkuara (data/burime/) në Neo4j si (:Chunk) për kërkim me vektorë.

  (:Chunk {tekst, burimi, seksioni, url, lloji: 'medlineplus'|'openfda', gjuha: 'en'})
  (:Chunk)-[:PERSHKRUAN]->(:Barna)        ← fletëudhëzuesit openFDA lidhen me ilaçin e bazës

Përdor të njëjtin indeks vektorial si PDF-të (chunk_embedding), kështu që kerko_ne_pdf() i gjen të gjitha.
Ekzekuto pas shkarko_datasetet.py:   python ngarko_burimet.py            (të gjitha)
                                     python ngarko_burimet.py openfda    (vetëm fletëudhëzuesit, më shpejt)
"""
import html
import json
import re
import sys
import xml.etree.ElementTree as ET

from config import EMBED_DIM, INDEKSI_PDF, ROOT, embed, kontrollo_lidhjen, query
from ngarko_pdf import ndaj_tekstin

DOSJA = ROOT / "data" / "burime"
PJESA = 64  # sa pjesë embed-ohen njëherësh

TITUJT_E_SEKSIONEVE = {
    "purpose": "Purpose", "indications_and_usage": "Uses", "do_not_use": "Do not use",
    "ask_doctor": "Ask a doctor before use if", "ask_doctor_or_pharmacist": "Ask a doctor or pharmacist before use if",
    "when_using": "When using this product", "stop_use": "Stop use and ask a doctor if",
    "pregnancy_or_breast_feeding": "Pregnancy or breast-feeding", "keep_out_of_reach_of_children": "Keep out of reach of children",
    "warnings": "Warnings", "dosage_and_administration": "Directions (US label)", "contraindications": "Contraindications",
    "warnings_and_cautions": "Warnings and precautions", "adverse_reactions": "Adverse reactions",
    "drug_interactions": "Drug interactions", "use_in_specific_populations": "Use in specific populations",
}


def _pa_html(tekst: str) -> str:
    tekst = re.sub(r"<\s*(br|/p|/li|/h\d)\s*/?>", "\n\n", tekst or "", flags=re.I)
    tekst = html.unescape(re.sub(r"<[^>]+>", " ", tekst))
    return "\n\n".join(" ".join(p.split()) for p in tekst.split("\n\n") if p.strip())


def pjeset_medlineplus() -> list[dict]:
    rrenja = ET.parse(DOSJA / "medlineplus_topics.xml").getroot()
    rows = []
    for t in rrenja.iter("health-topic"):
        if t.get("language") != "English":
            continue
        titulli, url = t.get("title"), t.get("url")
        emra = [a.text for a in t.findall("also-called") if a.text]
        grupet = [g.text for g in t.findall("group") if g.text]
        permbledhja = _pa_html(t.findtext("full-summary") or "")
        if len(permbledhja) < 80:
            continue
        koka = titulli + (f" (also called: {', '.join(emra)})" if emra else "")
        for i, pjese in enumerate(ndaj_tekstin(permbledhja)):
            rows.append({"tekst": f"{koka}. {pjese}" if i == 0 else f"{titulli}: {pjese}",
                         "burimi": f"MedlinePlus: {titulli}", "seksioni": ", ".join(grupet[:3]),
                         "url": url, "lloji": "medlineplus", "barna": None})
    return rows


def pjeset_openfda() -> list[dict]:
    etiketat = json.loads((DOSJA / "openfda_labels.json").read_text(encoding="utf-8"))
    rows = []
    for bid, e in etiketat.items():
        emri = e["emri"].title()
        for seksioni, tekst in e["seksionet"].items():
            titulli = TITUJT_E_SEKSIONEVE.get(seksioni, seksioni)
            tekst = " ".join(tekst.split())
            for pjese in ndaj_tekstin(tekst, madhesia=800, mbivendosja=100):
                rows.append({"tekst": f"{emri} — {titulli}: {pjese}", "burimi": f"openFDA: {emri}",
                             "seksioni": seksioni, "url": f"https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={e['set_id']}",
                             "lloji": "openfda", "barna": bid})
    return rows


def ngarko(rows: list[dict], lloji: str):
    query("MATCH (c:Chunk {lloji: $l}) DETACH DELETE c", l=lloji)
    for i in range(0, len(rows), PJESA):
        grupi = rows[i:i + PJESA]
        vektoret = embed([r["tekst"] for r in grupi])
        query("UNWIND $rows AS r "
              "CREATE (c:Chunk {tekst: r.tekst, burimi: r.burimi, seksioni: r.seksioni, url: r.url, "
              "                 lloji: r.lloji, gjuha: 'en'}) "
              "WITH c, r CALL db.create.setNodeVectorProperty(c, 'embedding', r.v) "
              "WITH c, r OPTIONAL MATCH (b:Barna {id: r.barna}) "
              "FOREACH (_ IN CASE WHEN b IS NULL THEN [] ELSE [1] END | MERGE (c)-[:PERSHKRUAN]->(b))",
              rows=[{**r, "v": v} for r, v in zip(grupi, vektoret)])
        print(f"  {lloji}: {min(i + PJESA, len(rows))}/{len(rows)}", flush=True)


def main():
    kontrollo_lidhjen()
    query(f"CREATE VECTOR INDEX {INDEKSI_PDF} IF NOT EXISTS FOR (c:Chunk) ON c.embedding "
          "OPTIONS {indexConfig: {`vector.dimensions`: " + str(EMBED_DIM) + ", "
          "`vector.similarity_function`: 'cosine'}}")
    query("CREATE INDEX chunk_lloji IF NOT EXISTS FOR (c:Chunk) ON (c.lloji)")
    zgjedhur = sys.argv[1:] or ["openfda", "medlineplus"]
    if "openfda" in zgjedhur:
        ngarko(pjeset_openfda(), "openfda")
    if "medlineplus" in zgjedhur:
        ngarko(pjeset_medlineplus(), "medlineplus")
    for r in query("MATCH (c:Chunk) RETURN c.lloji AS lloji, count(*) AS n ORDER BY lloji"):
        print(f"Gati: {r['n']} pjesë nga {r['lloji'] or 'pdf'}")


if __name__ == "__main__":
    main()
