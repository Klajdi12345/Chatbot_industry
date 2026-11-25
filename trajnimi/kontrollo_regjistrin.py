"""Kontrolli automatik i emrave të regjistrit AKBPM: cilët emra tregtarë ose lëndë ngatërrohen me fjalë të zakonshme?

    python -m trajnimi.kontrollo_regjistrin          → shkruan data/regjistri_perjashtime.json dhe raportin

Korpusi: tekstet shqip të projektit (njohuritë, sëmundjet, përgjigjet e botit, fjalorët, rastet e testit,
dokumentimi) dhe tekstet anglisht të MedlinePlus. Një çelës i regjistrit që kap një fjalë të korpusit
përjashtohet, përveç kur fjala është vetë emër ilaçi (njohurite.json, inn_en.json ose lëndë aktive e regjistrit).
Një emër i përjashtuar nuk humbet: produkti gjendet ende sipas lëndës aktive.
"""
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from config import ROOT, normalizo

DALJA = ROOT / "data" / "regjistri_perjashtime.json"
RAPORTI = ROOT / "trajnimi" / "raportet" / "regjistri_perjashtime.md"
SHQIP = ["data/njohurite.json", "data/semundjet.json", "data/perkthime_en.json", "data/fjalori_shqip.json",
         "data/fjalori_anglisht.json", "data/terma_en.json", "trajnimi/rastet.json", "trajnimi/mesimet.json",
         "chatbot.py", "dokumentimi/krijo_dokumentimin.py", "dokumentimi/krijo_databazen.py", "README.md"]
# Fjalë të zakonshme shqipe që nuk janë domosdoshmërisht në korpus (ditë, ushqime, trupi, folje të shpeshta).
FJALE_SHTESE = """
pasdite mengjes darke dreke mbremje sonte neser dje sot javen muajin vitin vjeç vjet ore minuta sekonda
mama babai djali vajza gruaja burri motra vellai gjyshi gjyshja femija femijet foshnja bebi shoku shoqja
koka sytë syri veshi hunda goja dhembet gjuha fyti qafa shpatulla krahu berryli dora gishti gjoksi barku
shpina mesi kofsha gjuri kemba thembra lekura floket thonjte zemra mushkerite melcia veshkat stomaku zorret
buka uji qumesht kafe caj sheqer kripe mish peshk perime fruta molla portokall limon banane domate patate
vere birra raki duhan cigare alkool ushqim pije gjume pune shkolle shtepi makine rruge dyqan farmaci spital
dhemb dhimbje temperature ethe kolle fryme marramendje lodhje dobesi te_vjella diarre kapsllek urth alergji
tableta shurup pomade krem pika sprej xhel kapsula injeksion recete farmacist mjek doktor infermiere
shume pak mire keq lehte rende shpejt ngadale tani gjithmone kurre ndonjehere perseri akoma
mund duhet dua kam jam eshte kemi keni kane merr marr pi ha fle punoj shkoj vij rri ngrihem shtrihem
normale ditore javore mujore vjetore natyrale kimike aktive pasive pozitive negative
""".split()


def _fjalet_nga(obj, dalja: list):
    if isinstance(obj, str):
        dalja.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            dalja.append(str(k))
            _fjalet_nga(v, dalja)
    elif isinstance(obj, list):
        for v in obj:
            _fjalet_nga(v, dalja)


def korpusi_shqip() -> list[str]:
    tekste = list(FJALE_SHTESE)
    for s in SHQIP:
        p = ROOT / s
        if not p.exists():
            continue
        if p.suffix == ".json":
            _fjalet_nga(json.loads(p.read_text(encoding="utf-8")), tekste)
        else:
            tekste += re.findall(r'"([^"\n]{3,})"', p.read_text(encoding="utf-8")) if p.suffix == ".py" \
                else [p.read_text(encoding="utf-8")]
    return tekste


def korpusi_anglisht() -> Counter:
    rrenja = ET.parse(ROOT / "data" / "burime" / "medlineplus_topics.xml").getroot()
    c = Counter()
    for t in rrenja.iter("health-topic"):
        if t.get("language") == "English":
            tekst = re.sub(r"<[^>]+>", " ", t.findtext("full-summary") or "")
            c.update(re.findall(r"[a-z]+", normalizo(tekst)))
    return c


def emrat_e_ilaceve() -> set[str]:
    """Çelësat e fjalëve që janë vetë emra ilaçesh (këto nuk janë ngatërresa)."""
    from regjistri import _fjalet, celes
    n = json.loads((ROOT / "data" / "njohurite.json").read_text(encoding="utf-8"))
    tekste = []
    for b in n["barnat"]:
        tekste += [b["id"].replace("_", " "), b["emer"], b.get("lende_aktive", ""), *b.get("emra_tregtare", [])]
    inn = json.loads((ROOT / "data" / "inn_en.json").read_text(encoding="utf-8"))
    tekste += [x for v in inn["inn"].values() for x in v]
    return {celes(f) for t in tekste for f in _fjalet(t)}


def main():
    import regjistri
    regjistri.perjashtimet.cache_clear()
    if DALJA.exists():
        DALJA.unlink()  # llogarit nga e para, pa përjashtimet e vjetra
    regjistri.indeksi.cache_clear()
    regjistri._sipas_shkronjave.cache_clear()
    ix = regjistri.indeksi()
    ilacet = emrat_e_ilaceve()
    lendet_njefjaleshe = {k[0] for k in ix["lende"] if len(k) == 1}

    perjashto: dict[str, list[str]] = {}

    def eshte_ilac(w: str) -> bool:
        return any(regjistri._perputhet(w, l) for l in ilacet | lendet_njefjaleshe if l[:3] == w[:3])

    def kontrollo(teksti: str, burimi: str):
        if re.search(r"\\b|\|", teksti):
            return  # shprehje të rregullta të kodit me lista ilaçesh (xanax|diazepam|...): jo tekst i zakonshëm
        for fjala in regjistri._fjalet(teksti):
            w = regjistri.celes(fjala)
            if len(w) < regjistri.MIN_GJATESIA or eshte_ilac(w):
                continue
            for tabela in (ix["emra"], ix["lende"]):
                for k in regjistri._kandidatet(w, tabela):
                    if len(k) == 1 and regjistri._perputhet(w, k[0]):
                        perjashto.setdefault(k[0], []).append(f"{burimi}: {fjala}")

    for t in korpusi_shqip():
        kontrollo(t, "shqip")
    for fjala, n in korpusi_anglisht().items():
        if n >= 3 and len(fjala) >= regjistri.MIN_GJATESIA:
            kontrollo(fjala, "anglisht")
    for k in regjistri.FJALE_JO_ILACE:
        perjashto.setdefault(k, []).append("lista e fjalëve kimike/mjekësore të përgjithshme")

    rreshta = []
    for k, burimet in sorted(perjashto.items()):
        produktet = ix["emra"].get(tuple(k.split())) or ix["lende"].get(tuple(k.split())) or []
        emri = produktet[0]["emri_tregtar"] if produktet else "?"
        rreshta.append(f"| `{k}` | {emri} | {len(produktet)} | {', '.join(sorted(set(burimet))[:3])} |")
    DALJA.write_text(json.dumps({
        "_pershkrimi": "Çelësa të regjistrit AKBPM që ngatërrohen me fjalë të zakonshme (krijuar nga "
                       "trajnimi/kontrollo_regjistrin.py). Këta emra nuk njihen vetëm nga një fjalë.",
        "celesat": sorted(perjashto)}, ensure_ascii=False, indent=1), encoding="utf-8")
    RAPORTI.parent.mkdir(exist_ok=True)
    RAPORTI.write_text("# Emrat e regjistrit që ngatërrohen me fjalë të zakonshme\n\n"
                       f"{len(perjashto)} çelësa u përjashtuan.\n\n| Çelësi | Produkti | Produkte | Burimi |\n|---|---|---|---|\n"
                       + "\n".join(rreshta) + "\n", encoding="utf-8")
    regjistri.perjashtimet.cache_clear()
    regjistri.indeksi.cache_clear()
    regjistri._sipas_shkronjave.cache_clear()
    ix = regjistri.indeksi()
    print(f"{len(perjashto)} çelësa u përjashtuan → {DALJA.name}; mbeten {len(ix['emra'])} emra tregtarë "
          f"dhe {len(ix['lende'])} lëndë aktive të kërkueshme")


if __name__ == "__main__":
    main()
