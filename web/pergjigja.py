"""Përgjigjja e botit (chatbot.Pergjigje) → JSON i pastër për ndërfaqen web.

Teksti pastrohet nga emoji-t (ndërfaqja ka ikonat e veta, të pakta dhe të njëtrajtshme).
Kartat përkthehen në anglisht kur personi shkruan anglisht (me kontrollin e numrave te perkthimi.py)."""
import re

from chatbot import Pergjigje
from perkthimi import perkthe_shume

_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿ℹ️‍⃣]")

FUSHAT_E_ILACIT = ("emer", "lende_aktive", "forma", "doza", "doza_maks", "kohezgjatja", "si_merret")

TITUJT_E_SEKSIONEVE = {
    "purpose": "Purpose", "indications_and_usage": "Uses", "do_not_use": "Do not use",
    "ask_doctor": "Ask a doctor before use if", "ask_doctor_or_pharmacist": "Ask a doctor or pharmacist before use if",
    "when_using": "When using this product", "stop_use": "Stop use and ask a doctor if",
    "pregnancy_or_breast_feeding": "Pregnancy or breast-feeding",
    "keep_out_of_reach_of_children": "Keep out of reach of children", "warnings": "Warnings",
    "dosage_and_administration": "Directions (US label)", "contraindications": "Contraindications",
    "warnings_and_cautions": "Warnings and precautions", "adverse_reactions": "Adverse reactions",
    "drug_interactions": "Drug interactions", "use_in_specific_populations": "Use in specific populations",
}


def pa_emoji(tekst: str) -> str:
    """Heq emoji-t dhe hapësirat që mbeten pas tyre, pa prekur shkronjat shqipe ose shenjat →."""
    rreshta = []
    for r in (tekst or "").split("\n"):
        r2 = _EMOJI.sub("", r)
        if r2 != r:
            r2 = re.sub(r"(^|\s)\*\*\s+(?=\S)", r"\1**", r2)   # "**🩺 Simptomat:**" → "**Simptomat:**"
            r2 = re.sub(r"(?<=\S)[ \t]{2,}", " ", r2)         # "- 🧠 Po mendoj" → "- Po mendoj"
            if not r[:1].isspace():
                r2 = r2.lstrip()
        rreshta.append(r2)
    return "\n".join(rreshta).strip()


def _ne_anglisht(p: Pergjigje) -> tuple[list, list, list]:
    """Kopje të kartave me fushat e përkthyera (cache te data/perkthime_en.json; numrat kontrollohen).
    Emrat tregtarë nuk përkthehen."""
    tekste = []
    for b in p.barnat:
        tekste += [b.get(k) or "" for k in FUSHAT_E_ILACIT] + list(b.get("paralajmerime") or []) + \
            list(b.get("efekte_anesore") or []) + \
            [x for k in b.get("kujdes_profili") or [] for x in (k["gjendje"], k["arsye"])]
    for x in p.te_perjashtuara:
        tekste += [x["emer"]] + [a["arsye"] for a in x["arsyet"]]
    for s in p.simptomat:
        tekste += [s["emer"]] + list(s["shenja_alarmi"])
    fjalori = dict(zip(tekste, perkthe_shume(tekste)))

    def t(x):
        return fjalori.get(x, x) if x else x

    barnat = [{**b, **{k: t(b.get(k)) for k in FUSHAT_E_ILACIT},
               "paralajmerime": [t(x) for x in b.get("paralajmerime") or []],
               "efekte_anesore": [t(x) for x in b.get("efekte_anesore") or []],
               "kujdes_profili": [{"gjendje": t(k["gjendje"]), "arsye": t(k["arsye"])}
                                  for k in b.get("kujdes_profili") or []]}
              for b in p.barnat]
    perjashtuara = [{"emer": t(x["emer"]), "arsyet": [{**a, "arsye": t(a["arsye"])} for a in x["arsyet"]]}
                    for x in p.te_perjashtuara]
    simptomat = [{**s, "emer": t(s["emer"]), "shenja_alarmi": [t(a) for a in s["shenja_alarmi"]]}
                 for s in p.simptomat]
    return barnat, perjashtuara, simptomat


def _emri_burimit(d: dict) -> str:
    return f"{d['burimi']} f.{d['faqja']}" if d.get("faqja") else d["burimi"]


def te_dhenat(p: Pergjigje) -> dict:
    """Gjithçka që i duhet ndërfaqes për ta shfaqur përgjigjen (dhe për ta rishfaqur më vonë)."""
    gjuha = getattr(p, "gjuha", "sq")
    if p.urgjence:
        barnat, perjashtuara, simptomat = [], [], []
    elif gjuha == "en":
        barnat, perjashtuara, simptomat = _ne_anglisht(p)
    else:
        barnat, perjashtuara, simptomat = p.barnat, p.te_perjashtuara, p.simptomat

    fleteudhezuesit = {}
    for d in getattr(p, "fleteudhezuesit", None) or []:
        f = fleteudhezuesit.setdefault(d["emer"], {"emer": d["emer"], "url": d.get("url"), "seksione": []})
        f["seksione"].append({"titull": TITUJT_E_SEKSIONEVE.get(d["seksioni"], d["seksioni"]),
                              "tekst": d["tekst"].split(": ", 1)[-1][:1200]})
    burime = {}
    for d in p.burime or []:
        burime.setdefault(_emri_burimit(d), d.get("url"))

    return {
        "tekst": pa_emoji(p.tekst),
        "urgjence": p.urgjence,
        "gjuha": gjuha,
        "sekonda": round(p.sekonda, 1),
        "hapat": [pa_emoji(h) for h in p.hapat or []],
        "mendimi": (p.mendimi_modelit or "")[-4000:],
        "pa_doza": p.pa_doza,
        "barnat": [{k: b.get(k) for k in (*FUSHAT_E_ILACIT, "emra_tregtare", "kujdes_profili",
                                           "paralajmerime", "efekte_anesore")} for b in barnat],
        "te_perjashtuara": [{"emer": x["emer"], "arsye": " ".join(a["arsye"] for a in x["arsyet"])}
                            for x in perjashtuara],
        "alarmi": [{"emer": s["emer"], "shenjat": list(s["shenja_alarmi"])} for s in simptomat if s.get("shenja_alarmi")],
        "fleteudhezuesit": list(fleteudhezuesit.values()),
        "burime": [{"emer": e, "url": u} for e, u in sorted(burime.items())],
    }
