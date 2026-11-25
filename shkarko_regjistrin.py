"""Regjistri zyrtar i barnave të autorizuara në Shqipëri (AKBPM) → data/regjistri_akbpm.json

    python shkarko_regjistrin.py                 → shkarkon PDF-në më të fundit nga akbpm.gov.al/publikime/
    python shkarko_regjistrin.py --pdf regjistri.pdf --otc lista.pdf → lexon PDF-të e shkarkuara më parë

Lista OTC: Urdhri i Ministrit të Shëndetësisë nr. 501, datë 3.7.2018 (Fletorja Zyrtare 2018/103), 813 barna.
"Në farmaci lejohet tregtimi pa recetë mjekësore vetëm i barnave që përfshihen në listën OTC": çdo produkt
i regjistrit që nuk është në këtë listë shënohet pa_recete = False (kërkon recetë).

Regjistri është një tabelë PDF (rreth 770 faqe) me kolonat: emri tregtar, forma/doza, lënda aktive (principi
aktiv), paketimi, mbajtësi i autorizimit, prodhuesi, urdhri i ministrit/data. Çdo rresht është një produkt.

Përdorimi në FarmaBot: INFORMACION (çfarë është ky ilaç, cila lëndë aktive, a është i autorizuar në Shqipëri).
Ilaçet me recetë nuk i sugjerohen kurrë personit; sugjerimet mbeten vetëm te ilaçet pa recetë të njohurite.json.
"""
import argparse
import json
import re
import tempfile
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DALJA = ROOT / "data" / "regjistri_akbpm.json"
DALJA_OTC = ROOT / "data" / "lista_otc.json"
FAQJA = "https://akbpm.gov.al/publikime/"
KOKA = {"User-Agent": "Mozilla/5.0 (FarmaBot; regjistri publik i barnave)"}
KOLONAT = ["emri_tregtar", "forma_doza", "lenda_aktive", "paketimi", "mbajtesi", "prodhuesi", "autorizimi"]


def gjej_lidhjen() -> str:
    html = requests.get(FAQJA, headers=KOKA, timeout=60).text
    lidhjet = re.findall(r'href="(https://akbpm\.gov\.al/wp-content/uploads/[^"]*REGJIST[^"]*BARNAVE[^"]*\.pdf)"', html, re.I)
    if not lidhjet:
        raise SystemExit(f"Nuk u gjet lidhja e regjistrit te {FAQJA}")
    return lidhjet[0]


def gjej_lidhjen_otc() -> str:
    html = requests.get(FAQJA, headers=KOKA, timeout=60).text
    m = re.search(r'Lista e Barnave pa Recet[eë]\s*:?\s*<a href="([^"]+\.pdf)"', html, re.I)
    if not m:
        raise SystemExit(f"Nuk u gjet lidhja e listës OTC te {FAQJA}")
    return m.group(1)


def _pastro(qeliza) -> str:
    t = (qeliza or "").replace("�", "ë")          # PDF-ja e humb "ë"-në (shfaqet si �)
    return " ".join(t.split())


def lexo_pdf(skedari: Path, on_progres=None) -> list[dict]:
    import pdfplumber
    produktet = []
    with pdfplumber.open(str(skedari)) as pdf:
        n = len(pdf.pages)
        for i, faqja in enumerate(pdf.pages, 1):
            for tabela in faqja.extract_tables():
                for rresht in tabela:
                    if not rresht or len(rresht) < 7:
                        continue
                    qelizat = [_pastro(x) for x in rresht[:7]]
                    if not qelizat[0] or qelizat[0].upper().startswith("EMRI TREGTAR"):
                        continue
                    p = dict(zip(KOLONAT, qelizat))
                    p["faqja"] = i
                    produktet.append(p)
            if on_progres and i % 25 == 0:
                on_progres(i, n)
    return produktet


def lexo_otc(skedari: Path) -> list[dict]:
    """Lista zyrtare e barnave pa recetë: Nr, emri tregtar, forma-doza, lënda vepruese, paketimi."""
    import pdfplumber
    lista = {}
    with pdfplumber.open(str(skedari)) as pdf:
        for faqja in pdf.pages:
            for tabela in faqja.extract_tables():
                for r in tabela:
                    if r and len(r) >= 5 and r[0] and str(r[0]).strip().isdigit():
                        nr = int(str(r[0]).strip())
                        lista[nr] = {"nr": nr, "emri_tregtar": _pastro(r[1]), "forma_doza": _pastro(r[2]),
                                     "lenda_aktive": _pastro(r[3]), "paketimi": _pastro(r[4])}
    mungojne = sorted(set(range(1, max(lista) + 1)) - set(lista)) if lista else []
    if mungojne:
        print(f"KUJDES: mungojnë rreshtat e listës OTC {mungojne[:20]}")
    return [lista[k] for k in sorted(lista)]


def _celes(emri: str) -> str:
    """Emri tregtar pa dozë dhe shenja: "ACC AKUT 600 MG" → "ACC AKUT"."""
    e = re.sub(r"\b\d+([.,]\d+)?\s*(mg|g|ml|mcg|µg|iu|%).*$", "", emri.upper(), flags=re.I)
    return " ".join(re.sub(r"[^A-Z0-9 ]", " ", e).split())


def _lende(t: str) -> frozenset:
    return frozenset(x for x in re.split(r"[^A-Z]+", t.upper()) if len(x) > 3)


def sheno_otc(produktet: list[dict], otc: list[dict]) -> int:
    """pa_recete=True kur emri tregtar dhe lënda aktive përputhen me një rresht të listës OTC."""
    sipas_emrit = {}
    for o in otc:
        sipas_emrit.setdefault(_celes(o["emri_tregtar"]), []).append(_lende(o["lenda_aktive"]))
    n = 0
    for p in produktet:
        lende = _lende(p["lenda_aktive"])
        p["pa_recete"] = any(l & lende for l in sipas_emrit.get(_celes(p["emri_tregtar"]), []))
        n += p["pa_recete"]
    return n


def pasuro(p: dict) -> dict:
    """Fusha të nxjerra: forma (pa dozën), doza, lëndët aktive si listë, data e autorizimit."""
    fd = p["forma_doza"]
    forma, _, doza = fd.partition(" x ")
    p["forma"] = forma.strip()
    p["doza"] = doza.strip()
    p["lendet"] = [x.strip() for x in re.split(r"\s*(?:\+|/|;| and | & )\s*", p["lenda_aktive"]) if x.strip()]
    if m := re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", p["autorizimi"]):
        p["data_autorizimit"] = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return p


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--pdf", type=Path, help="PDF e regjistrit, e shkarkuar më parë (përndryshe shkarkohet)")
    a.add_argument("--otc", type=Path, help="PDF e listës OTC, e shkarkuar më parë (përndryshe shkarkohet)")
    args = a.parse_args()
    if args.pdf:
        skedari, burimi = args.pdf, str(args.pdf)
    else:
        burimi = gjej_lidhjen()
        print(f"Po shkarkoj {burimi}")
        skedari = Path(tempfile.mkdtemp(prefix="akbpm_")) / "regjistri.pdf"
        r = requests.get(burimi, headers=KOKA, timeout=300)
        r.raise_for_status()
        skedari.write_bytes(r.content)
    produktet = [pasuro(p) for p in lexo_pdf(skedari, lambda i, n: print(f"\r  faqja {i}/{n}", end="", flush=True))]
    print()
    if args.otc:
        skedari_otc, burimi_otc = args.otc, str(args.otc)
    else:
        burimi_otc = gjej_lidhjen_otc()
        skedari_otc = skedari.with_name("lista_otc.pdf")
        r = requests.get(burimi_otc, headers=KOKA, timeout=300)
        r.raise_for_status()
        skedari_otc.write_bytes(r.content)
    otc = lexo_otc(skedari_otc)
    DALJA_OTC.write_text(json.dumps({"burimi": burimi_otc, "urdhri": "Nr. 501, datë 3.7.2018 (FZ 2018/103)",
                                     "barna": len(otc), "lista": otc}, ensure_ascii=False, indent=1), encoding="utf-8")
    n_otc = sheno_otc(produktet, otc)
    print(f"Lista OTC: {len(otc)} barna; {n_otc} produkte të regjistrit u shënuan pa recetë")
    lendet =sorted({l.upper() for p in produktet for l in p["lendet"]})
    DALJA.write_text(json.dumps({
        "burimi": burimi, "shkarkuar": datetime.now().strftime("%Y-%m-%d"),
        "produkte": len(produktet), "lende_aktive": len(lendet), "produktet": produktet,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"U ruajt {DALJA}: {len(produktet)} produkte, {len(lendet)} lëndë aktive të ndryshme")


if __name__ == "__main__":
    main()
