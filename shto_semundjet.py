"""Shton hyrje të reja te data/semundjet.json, pa dyfishime, me kopje rezervë dhe validim në fund.

    python shto_semundjet.py data/shtesa/thyerjet_2026-11-24.json [data/shtesa/kronike_2026-11-24.json ...]
    python shto_semundjet.py ... --icd-lista icd10cm_order_2026.txt   → edhe krahasim i kodeve me një listë zyrtare

Para shtimit: kopje rezervë data/semundjet_backup_<data>.json (nëse ekziston, shtohet ora).
Një hyrje NUK shtohet nëse emri_shqip, kodi_icd10 (përveç PER_VERIFIKIM) ose id ekziston tashmë.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from valido_semundjet import ICD10, PER_VERIFIKIM, SKEDARI, normalizo

ROOT = Path(__file__).resolve().parent


def kopje_rezerve(skedari: Path) -> Path:
    dita = datetime.now().strftime("%Y-%m-%d")
    rezerva = skedari.with_name(f"{skedari.stem}_backup_{dita}{skedari.suffix}")
    if rezerva.exists():
        rezerva = skedari.with_name(f"{skedari.stem}_backup_{dita}_{datetime.now():%H%M%S}{skedari.suffix}")
    shutil.copy2(skedari, rezerva)
    return rezerva


def kodet_zyrtare(lista: Path) -> set[str]:
    """Kodet nga skedari 'order' i ICD-10 (CMS): kolona 2, p.sh. 'S525' → 'S52.5'."""
    kodet = set()
    for rresht in lista.read_text(encoding="latin-1").splitlines():
        pjeset = rresht.split()
        if len(pjeset) >= 2 and re.fullmatch(r"[A-Z]\d{2}[0-9A-Z]*", pjeset[1]):
            k = pjeset[1]
            kodet.add(k if len(k) == 3 else f"{k[:3]}.{k[3:]}")
    return kodet


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("shtesat", nargs="+", type=Path, help="skedarë JSON me listë hyrjesh të reja")
    a.add_argument("--icd-lista", type=Path, help="lista e kodeve ICD-10 për krahasim (skedari 'order' i CMS)")
    args = a.parse_args()

    dataset = json.loads(SKEDARI.read_text(encoding="utf-8"))
    para = len(dataset["hyrjet"])
    emrat = {normalizo(h["emri_shqip"]) for h in dataset["hyrjet"]}
    kodet = {h["kodi_icd10"] for h in dataset["hyrjet"] if h.get("kodi_icd10") != PER_VERIFIKIM}
    ids = {h["id"] for h in dataset["hyrjet"]}

    te_reja, te_kapercyera = [], []
    for skedari in args.shtesat:
        for h in json.loads(skedari.read_text(encoding="utf-8")):
            arsye = []
            if normalizo(h.get("emri_shqip", "")) in emrat:
                arsye.append("emri ekziston")
            if h.get("kodi_icd10") != PER_VERIFIKIM and h.get("kodi_icd10") in kodet:
                arsye.append(f"kodi {h.get('kodi_icd10')} ekziston")
            if h.get("id") in ids:
                arsye.append("id ekziston")
            if arsye:
                te_kapercyera.append((h.get("id"), ", ".join(arsye)))
                continue
            te_reja.append(h)
            emrat.add(normalizo(h["emri_shqip"]))
            ids.add(h["id"])
            if h.get("kodi_icd10") != PER_VERIFIKIM:
                kodet.add(h["kodi_icd10"])

    rezerva = kopje_rezerve(SKEDARI)
    dataset["hyrjet"].extend(te_reja)
    SKEDARI.write_text(json.dumps(dataset, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Kopja rezervë: {rezerva.name}")
    print(f"Para: {para} hyrje · u shtuan: {len(te_reja)} · u kapërcyen (dyfishime): {len(te_kapercyera)} · "
          f"tani: {len(dataset['hyrjet'])}")
    for i, arsye in te_kapercyera:
        print(f"  kapërcyer {i}: {arsye}")

    if args.icd_lista:
        zyrtare = kodet_zyrtare(args.icd_lista)
        mungojne = [(h["id"], h["kodi_icd10"]) for h in dataset["hyrjet"]
                    if ICD10.match(h["kodi_icd10"]) and h["kodi_icd10"] not in zyrtare]
        print(f"Krahasimi me {args.icd_lista.name} ({len(zyrtare)} kode): "
              f"{len(mungojne)} kode nuk gjenden" + (":" if mungojne else ""))
        for i, k in mungojne:
            print(f"  {k}  ({i})")

    r = subprocess.run([sys.executable, str(ROOT / "valido_semundjet.py")], cwd=ROOT)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
