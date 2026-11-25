"""Validimi i dataset-it të thyerjeve dhe sëmundjeve (data/semundjet.json).

    python valido_semundjet.py                     → kontrollon dhe shkruan validation_report.md
    python valido_semundjet.py --skedari tjeter.json

Kontrollon: skemën, fushat e detyrueshme dhe bosh, dyfishimet (sipas emrit dhe kodit ICD-10), formatin e
kodeve ICD-10, mospërputhjet (kategoria kundrejt kapitullit ICD-10, koha e shërimit), dhe termat jo të
njëtrajtshëm. NUK ndryshon asgjë: vetëm raporton. Kthen kodin 1 nëse ka gabime.
"""
import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKEDARI = ROOT / "data" / "semundjet.json"
RAPORTI = ROOT / "validation_report.md"

FUSHAT = {  # fusha: lloji
    "id": str, "emri_shqip": str, "emri_anglisht": str, "kodi_icd10": str, "kategoria": str,
    "pjesa_e_trupit_ose_sistemi": str, "pershkrimi": str, "shkaqet": list, "faktoret_e_rrezikut": list,
    "simptomat": list, "shenjat_urgjente": list, "diagnoza": list, "trajtimi_konservativ": list,
    "trajtimi_kirurgjik": list, "koha_e_sherimit": dict, "komplikimet": list, "parandalimi": list,
    "burimi": str, "data_e_shtimit": str,
}
# Lista që mund të jenë bosh me arsye (p.sh. shumë sëmundje kronike s'kanë trajtim kirurgjik).
MUND_BOSH = {"trajtimi_kirurgjik"}
KATEGORITE = {"thyerje", "sëmundje"}
PER_VERIFIKIM = "PER_VERIFIKIM"
# ICD-10 i OBSH-së: shkronjë + 2 shifra, opsionalisht pikë + 1–2 shifra (p.sh. S52.5, E11, I10).
ICD10 = re.compile(r"^[A-TV-Z]\d{2}(\.\d{1,2})?$")
SISTEMET = {"skeletor", "kardiovaskular", "respirator", "nervor", "endokrin", "tretës", "urinar", "riprodhues",
            "lëkura", "imunitar", "gjaku", "muskulor-skeletor", "psikik", "syri", "veshi", "metabolik"}


def normalizo(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).split())


def valido(dataset: dict) -> dict:
    gabime, paralajmerime, per_verifikim = [], [], []
    hyrjet = dataset.get("hyrjet")
    if not isinstance(hyrjet, list):
        return {"gabime": ["Mungon lista 'hyrjet' në rrënjë të skedarit."], "paralajmerime": [],
                "per_verifikim": [], "hyrje": 0}
    sipas_emrit, sipas_kodit, sipas_id = defaultdict(list), defaultdict(list), defaultdict(list)
    for i, h in enumerate(hyrjet):
        emri = h.get("emri_shqip") or f"#{i}"
        vend = f"`{h.get('id', '?')}` ({emri})"
        # skema dhe fushat
        for f, lloji in FUSHAT.items():
            if f not in h:
                gabime.append(f"{vend}: mungon fusha `{f}`")
            elif not isinstance(h[f], lloji):
                gabime.append(f"{vend}: `{f}` duhet të jetë {lloji.__name__}, është {type(h[f]).__name__}")
            elif not h[f] and f not in MUND_BOSH:
                gabime.append(f"{vend}: fusha `{f}` është bosh")
            elif isinstance(h[f], list) and any(not str(x).strip() for x in h[f]):
                gabime.append(f"{vend}: `{f}` ka elemente bosh")
        for f in h:
            if f not in FUSHAT:
                paralajmerime.append(f"{vend}: fushë e panjohur `{f}`")
        # kodi ICD-10
        kodi = str(h.get("kodi_icd10") or "").strip()
        if kodi == PER_VERIFIKIM:
            per_verifikim.append(f"{vend}: kodi ICD-10 duhet verifikuar")
        elif kodi and not ICD10.match(kodi):
            gabime.append(f"{vend}: kodi ICD-10 `{kodi}` nuk ka formatin e saktë (p.sh. S52.5, E11, I10)")
        # kategoria kundrejt kapitullit ICD-10 (thyerjet janë te kapitulli XIX: S/T)
        kat = h.get("kategoria")
        if kat and kat not in KATEGORITE:
            gabime.append(f"{vend}: kategoria `{kat}` duhet të jetë një nga {sorted(KATEGORITE)}")
        if kat == "thyerje" and ICD10.match(kodi) and kodi[0] not in "ST":
            gabime.append(f"{vend}: klasifikuar si thyerje, por kodi `{kodi}` nuk është te kapitulli S/T (lëndime)")
        if kat == "sëmundje" and ICD10.match(kodi) and kodi[0] in "ST":
            paralajmerime.append(f"{vend}: klasifikuar si sëmundje, por kodi `{kodi}` është kod lëndimi (S/T)")
        # koha e shërimit: {"min": javë, "max": javë, "njesia": "javë"}
        k = h.get("koha_e_sherimit")
        if isinstance(k, dict) and k:
            if k.get("njesia") != "javë":
                gabime.append(f"{vend}: koha_e_sherimit duhet në javë (`njesia`: \"javë\"), jo `{k.get('njesia')}`")
            mn, mx = k.get("min"), k.get("max")
            kronike = mn is None and mx is None
            if kronike and (kat != "sëmundje" or "kronike" not in str(k.get("shenim", "")).lower()):
                gabime.append(f"{vend}: koha_e_sherimit pa interval lejohet vetëm për sëmundje kronike "
                              f"(me `shenim` që përmban \"kronike\")")
            elif kronike:
                pass
            elif not all(isinstance(x, (int, float)) for x in (mn, mx)):
                gabime.append(f"{vend}: koha_e_sherimit duhet të ketë `min` dhe `max` si numra")
            elif mn < 0 or mn > mx:
                gabime.append(f"{vend}: koha_e_sherimit ka interval të pasaktë ({mn}–{mx})")
        # data
        d = str(h.get("data_e_shtimit") or "")
        try:
            date.fromisoformat(d)
        except ValueError:
            gabime.append(f"{vend}: data_e_shtimit `{d}` duhet në formatin VVVV-MM-DD")
        # sistemi / termat e njëtrajtshëm
        s = normalizo(h.get("pjesa_e_trupit_ose_sistemi", ""))
        if s and s not in {normalizo(x) for x in SISTEMET}:
            paralajmerime.append(f"{vend}: sistemi `{h.get('pjesa_e_trupit_ose_sistemi')}` nuk është në listën "
                                 f"e termave të njëtrajtshëm ({', '.join(sorted(SISTEMET))})")
        sipas_emrit[normalizo(h.get("emri_shqip", ""))].append(vend)
        if ICD10.match(kodi):
            sipas_kodit[kodi].append(vend)
        sipas_id[h.get("id")].append(vend)
    for emri, v in sipas_emrit.items():
        if emri and len(v) > 1:
            gabime.append(f"Dyfishim sipas emrit: {', '.join(v)}")
    for kodi, v in sipas_kodit.items():
        if len(v) > 1:
            gabime.append(f"Dyfishim sipas kodit ICD-10 `{kodi}`: {', '.join(v)}")
    for i, v in sipas_id.items():
        if len(v) > 1:
            gabime.append(f"Dyfishim i id-së `{i}`: {', '.join(v)}")
    return {"gabime": gabime, "paralajmerime": paralajmerime, "per_verifikim": per_verifikim, "hyrje": len(hyrjet)}


def raporti_md(rez: dict, skedari: Path, struktura: str) -> str:
    rr = [f"# Raporti i validimit: `{skedari.relative_to(ROOT) if skedari.is_relative_to(ROOT) else skedari}`",
          "", f"Data: {date.today().isoformat()}", "", "## Struktura", "", struktura, "",
          f"## Përmbledhje", "", f"- Hyrje: **{rez['hyrje']}**", f"- Gabime: **{len(rez['gabime'])}**",
          f"- Paralajmërime: **{len(rez['paralajmerime'])}**", f"- PER_VERIFIKIM: **{len(rez['per_verifikim'])}**", ""]
    for titulli, celes in (("Gabime", "gabime"), ("Paralajmërime", "paralajmerime"), ("Për verifikim", "per_verifikim")):
        rr += [f"## {titulli}", ""] + ([f"- {x}" for x in rez[celes]] or ["Asnjë."]) + [""]
    return "\n".join(rr)


def struktura(dataset: dict, skedari: Path) -> str:
    h = dataset.get("hyrjet") or []
    fushat = ", ".join(f"`{f}` ({t.__name__})" for f, t in FUSHAT.items())
    return (f"- Formati: JSON, UTF-8 ({skedari.stat().st_size} bajt)\n"
            f"- Rrënja: {', '.join(f'`{k}`' for k in dataset)}; hyrjet janë te `hyrjet` (listë)\n"
            f"- Rreshta (hyrje): {len(h)}\n- Fushat e skemës: {fushat}\n"
            f"- `koha_e_sherimit`: {{\"min\": javë, \"max\": javë, \"njesia\": \"javë\"}}; për sëmundjet kronike "
            f"{{\"min\": null, \"max\": null, \"njesia\": \"javë\", \"shenim\": \"kronike: ...\"}}\n"
            f"- `kategoria`: {' / '.join(sorted(KATEGORITE))}; `kodi_icd10`: format OBSH (p.sh. S52.5) ose `{PER_VERIFIKIM}`")


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--skedari", type=Path, default=SKEDARI)
    a.add_argument("--raporti", type=Path, default=RAPORTI)
    args = a.parse_args()
    dataset = json.loads(args.skedari.read_text(encoding="utf-8"))
    rez = valido(dataset)
    args.raporti.write_text(raporti_md(rez, args.skedari, struktura(dataset, args.skedari)), encoding="utf-8")
    print(f"{rez['hyrje']} hyrje · {len(rez['gabime'])} gabime · {len(rez['paralajmerime'])} paralajmërime · "
          f"{len(rez['per_verifikim'])} PER_VERIFIKIM → {args.raporti}")
    sys.exit(1 if rez["gabime"] else 0)


if __name__ == "__main__":
    main()
