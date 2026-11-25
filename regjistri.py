"""Regjistri zyrtar i barnave të autorizuara në Shqipëri (AKBPM) për FarmaBot-in: VETËM INFORMACION.

    from regjistri import gjej, pergjigje
    gjetja = gjej("çfarë është augmentin?")   → {"lloji": "emer", "celesi": "augmentin", "produktet": [...]}
    pergjigje(gjetja)                          → tekst markdown shqip

Burimet: data/regjistri_akbpm.json (4530 produkte, shkarko_regjistrin.py) dhe lista ligjore OTC
(Urdhri 501/3.7.2018, data/lista_otc.json). Rregullat e sigurisë:
  * ilaçet me recetë NUK sugjerohen kurrë dhe për to nuk jepet asnjë dozë: vetëm çfarë janë, lënda aktive,
    format e autorizuara dhe që duhen marrë vetëm me recetë të mjekut;
  * edhe për produktet e listës OTC që nuk janë te njohurite.json nuk jepet dozë (s'kemi dozë të verifikuar):
    personi dërgohet te fletëudhëzuesi dhe farmacisti.
Kërkimi bëhet pa model gjuhësor: emrat krahasohen me një "çelës shqiptimi" (x→ks, c→k, ph→f, w→v...),
që "amoksicilinë", "Amoxicillin" dhe "amoksicilina" të jenë e njëjta lëndë.
"""
import json
import re
from collections import defaultdict
from functools import lru_cache

from config import ROOT, normalizo

SKEDARI = ROOT / "data" / "regjistri_akbpm.json"
SKEDARI_PERJASHTIMEVE = ROOT / "data" / "regjistri_perjashtime.json"
MIN_GJATESIA = 5     # çelës më i shkurtër se kaq ngatërrohet lehtë me fjalë të zakonshme
MAKS_PRAPASHTESA = 3  # "augmentin-in", "ibuprofen-i": prapashtesa e shquar shqipe
MAKS_FORMA = 5        # sa forma/doza tregohen në përgjigje

# Fjalë që vetëm nuk e dallojnë një produkt ("APO-...", "VITAMINA C") → përdoren dy fjalët e para.
FJALE_TE_PERGJITHSHME = {
    "co", "apo", "neo", "pms", "sodio", "sodium", "vitamina", "vitamine", "vitamin", "klorur", "chloride", "ringer",
    "acid", "acidum", "acido", "human", "humana", "potassium", "kalium", "calcium", "kalcium", "magnesium", "zinc",
    "ferrous", "iron", "insulin", "glucose", "glukoze", "glucosio", "solution", "solucion", "uje", "water", "aqua",
    "baby", "forte", "plus", "duo", "mono", "retard", "junior", "kids", "total", "extra", "max", "ultra", "new",
    "dr", "doctor", "pharma", "kripe", "sterile", "sol", "sirup", "crema", "gel", "spray", "alpha", "beta", "omega",
}
# Fjalë kimike/mjekësore të përgjithshme që janë edhe "lëndë" ose emra në regjistër, por në bisedë kanë
# kuptim tjetër ("bakteret", "dehidratimi", "proteina", "sinusi", "alergji"): nuk njihen si ilaç.
FJALE_JO_ILACE = {
    "bakter", "dehidrat", "eksces", "ekstrakt", "komon", "kompleks", "oksid", "protein", "strain", "karbonat",
    "hidroksid", "bikarbonat", "aluminium", "sulfat", "glukonat", "alerg", "alkol", "medikal", "moment", "proton",
    "sinus", "fungus", "feritin", "algin", "kolagen", "vitamin a", "mineral", "natural", "herbal", "tonik", "fitness",
}
# Kripërat dhe format kimike: hiqen nga emri i lëndës aktive ("AMOXICILLIN TRIHYDRATE" → "amoxicillin").
KRIPERAT = {
    "hydrochloride", "hydrochlorid", "dihydrochloride", "hcl", "hydrobromide", "sodium", "disodium", "potassium",
    "calcium", "magnesium", "sulphate", "sulfate", "maleate", "fumarate", "hemifumarate", "tartrate", "bitartrate",
    "citrate", "acetate", "mesylate", "mesilate", "besylate", "besilate", "succinate", "phosphate", "dihydrate",
    "monohydrate", "trihydrate", "hemihydrate", "sesquihydrate", "pentahydrate", "anhydrous", "nitrate",
    "propionate", "dipropionate", "valerate", "furoate", "bromide", "lysine", "salt", "medoxomil", "axetil",
    "dimesylate", "hyclate", "hydrate", "arginine", "tromethamine", "trometamol", "pivoxil", "estolate",
    "stearate", "palmitate", "lactate", "gluconate", "embonate", "oxalate", "decanoate", "enanthate",
}
_RE_SQARIM = re.compile(r"\(\s*as [^)]*\)|\bas [a-z][^+;,]*", re.I)
_RE_SASI = re.compile(r"\bx\s*[\d.,]+\s*\S*|\d+([.,]\d+)?\s*(mg|mcg|µg|g|ml|iu|ui|%|mmol|meq)\b[^+]*", re.I)


def celes(fjala: str) -> str:
    """Çelësi i shqiptimit: 'Amoxicillin' → 'amoksicilin', 'amoksicilinë' → 'amoksicilin'."""
    t = normalizo(fjala)
    t = re.sub(r"[^a-z0-9]", "", t)
    if len(t) <= 2:
        return t  # "c" te "vitamina C" mbetet "c" (jo "k")
    for a, b in (("ph", "f"), ("th", "t"), ("ck", "k"), ("qu", "kv"), ("x", "ks"), ("y", "i"), ("w", "v")):
        t = t.replace(a, b)
    t = re.sub(r"c(?![eik])", "k", t)          # c para a/o/u/bashkëtingëllores lexohet k (diclofenac)
    t = re.sub(r"(.)\1+", r"\1", t)              # shkronja të dyfishta
    return re.sub(r"[aeiou]+$", "", t) if len(t) > 3 else t


def emri_i_lendes(lenda: str) -> str:
    """'AMOXICILLIN x 250mg (as AMOXICILLIN TRIHYDRATE)' → 'AMOXICILLIN'."""
    t = _RE_SASI.sub(" ", _RE_SQARIM.sub(" ", lenda))
    fjale = [f for f in re.split(r"[\s,]+", t) if f]
    pa_kripe = [f for f in fjale if f.lower() not in KRIPERAT]
    return " ".join(pa_kripe or fjale).strip(" -")


def _fjalet(tekst: str) -> list[str]:
    return [f for f in re.split(r"[^a-z0-9]+", normalizo(tekst)) if f]


def _celesi_i_emrit(fjalet: list[str]) -> list[str]:
    """Fjalët që e dallojnë emrin: e para, ose dy të parat kur e para është e përgjithshme."""
    fjalet = [f for f in fjalet if not re.fullmatch(r"\d+([a-z]{1,3})?", f)]
    if not fjalet:
        return []
    if fjalet[0] in FJALE_TE_PERGJITHSHME or len(celes(fjalet[0])) < MIN_GJATESIA:
        return fjalet[:2] if len(fjalet) >= 2 else []
    return fjalet[:1]


@lru_cache
def perjashtimet() -> frozenset:
    """Çelësa emrash tregtarë që janë edhe fjalë të zakonshme (shiko trajnimi/kontrollo_regjistrin.py)."""
    try:
        return frozenset(json.loads(SKEDARI_PERJASHTIMEVE.read_text(encoding="utf-8"))["celesat"])
    except FileNotFoundError:
        return frozenset()


@lru_cache
def indeksi() -> dict:
    """{"emra": {çelës: [produkte]}, "lende": {çelës: [produkte]}, "emrat_e_lendeve": {çelës: emër}}.
    Çelësi i shumëfjalëshëm është tuple çelësash ("vitamin", "c")."""
    d = json.loads(SKEDARI.read_text(encoding="utf-8"))
    emra, lende, emrat_e_lendeve = defaultdict(list), defaultdict(list), {}
    for p in d["produktet"]:
        for l in p.get("lendet") or [p["lenda_aktive"]]:
            emri = emri_i_lendes(l)
            k = tuple(celes(f) for f in _celesi_i_emrit(_fjalet(emri)))
            if k and len("".join(k)) >= MIN_GJATESIA and " ".join(k) not in perjashtimet():
                lende[k].append(p)
                emrat_e_lendeve.setdefault(k, emri)
    for p in d["produktet"]:
        k = tuple(celes(f) for f in _celesi_i_emrit(_fjalet(p["emri_tregtar"])))
        if not k or len("".join(k)) < MIN_GJATESIA or k in lende:
            continue  # emri tregtar = emri i lëndës ("PARACETAMOL KRKA"): gjendet si lëndë
        if " ".join(k) not in perjashtimet():
            emra[k].append(p)
    return {"emra": dict(emra), "lende": dict(lende), "emrat_e_lendeve": emrat_e_lendeve,
            "produkte": len(d["produktet"]), "burimi": "AKBPM", "shkarkuar": d.get("shkarkuar")}


def _perputhet(fjala: str, k: str) -> int:
    """2 = njësoj, 1 = me prapashtesë shqipe ('augmentinin'), 0 = jo."""
    if fjala == k:
        return 2
    if len(k) >= MIN_GJATESIA and len(fjala) - len(k) <= MAKS_PRAPASHTESA:
        # "adenurici" → çelësi "adenurici" (c para i mbetet c), emri "adenurik": krahasohen me c = k.
        if fjala.startswith(k) or fjala.replace("c", "k").startswith(k.replace("c", "k")):
            return 1
    return 0


def _kerko(celesat: list[str], tabela: dict) -> list[tuple[int, tuple]]:
    """(përputhja, çelësi) për çdo çelës të tabelës që gjendet te teksti (si varg fjalësh njëra pas tjetrës)."""
    gjetje = []
    for i, f in enumerate(celesat):
        for k in _kandidatet(f, tabela):
            n = len(k)
            if celesat[i:i + n - 1] == list(k[:-1]) and i + n - 1 < len(celesat):
                p = _perputhet(celesat[i + n - 1], k[-1]) if n > 1 else _perputhet(f, k[0])
                if p:
                    gjetje.append((p + n, k))  # më shumë fjalë = më e sigurt
    return gjetje


@lru_cache
def _sipas_shkronjave(lloji: str) -> dict:
    """Çelësat sipas 3 shkronjave të para të fjalës së parë, që kërkimi të mos kalojë 4000 çelësa çdo herë."""
    grupet = defaultdict(list)
    for k in indeksi()[lloji]:
        grupet[k[0][:3]].append(k)
    return dict(grupet)


def _kandidatet(fjala: str, tabela: dict) -> list[tuple]:
    lloji = "emra" if tabela is indeksi()["emra"] else "lende"
    return _sipas_shkronjave(lloji).get(fjala[:3], [])


def gjej(tekst: str, variantet: list[str] | None = None) -> dict | None:
    """Produkti ose lënda aktive e përmendur te teksti (më e sigurta), ose None."""
    ix = indeksi()
    teksti = " ".join(dict.fromkeys([tekst, *(variantet or [])]))
    celesat = [celes(f) for f in _fjalet(teksti)]
    gjetje = [(p, k, "emer") for p, k in _kerko(celesat, ix["emra"])]
    gjetje += [(p, k, "lende") for p, k in _kerko(celesat, ix["lende"])]
    if not gjetje:
        return None
    # Më e mira: përputhja më e saktë, pastaj çelësi më i gjatë, pastaj emri tregtar para lëndës.
    p, k, lloji = max(gjetje, key=lambda g: (g[0], len("".join(g[1])), g[2] == "emer"))
    produktet = ix["emra" if lloji == "emer" else "lende"][k]
    return {"lloji": lloji, "celesi": k, "produktet": produktet,
            "emri": ix["emrat_e_lendeve"].get(k) if lloji == "lende" else produktet[0]["emri_tregtar"]}


# ---------------------------------------------------------------- përgjigjja
FORMAT = {  # format më të shpeshta të regjistrit, në shqip
    "film coated tablets": "tableta të veshura me film", "film-coated tablets": "tableta të veshura me film",
    "film-coated tablet": "tableta të veshura me film", "film coated tablet": "tableta të veshura me film",
    "tablets": "tableta", "tablet": "tableta", "coated tablets": "tableta të veshura",
    "sugar coated tablets": "tableta të veshura me sheqer", "chewable tablets": "tableta për t'u përtypur",
    "effervescent tablets": "tableta shkumuese", "orodispersible tablets": "tableta që treten në gojë",
    "dispersible tablets": "tableta që treten në ujë", "gastro-resistant tablets": "tableta gastrorezistente",
    "prolonged release tablets": "tableta me çlirim të zgjatur", "prolonged-release tablets": "tableta me çlirim të zgjatur",
    "hard capsules": "kapsula të forta", "hard capsule": "kapsula të forta", "capsules": "kapsula", "capsule": "kapsula",
    "soft capsules": "kapsula të buta", "gastro-resistant hard capsules": "kapsula gastrorezistente",
    "solution for injection": "solucion për injeksion", "solution for infusion": "solucion për infuzion",
    "concentrate for solution for infusion": "koncentrat për infuzion", "syrup": "shurup",
    "oral solution": "solucion oral", "oral suspension": "suspension oral", "cream": "krem", "gel": "xhel",
    "ointment": "pomadë", "eye drops, solution": "pika për sytë", "eye drops solution": "pika për sytë",
    "eye ointment": "pomadë për sytë", "suppositories": "supozitorë", "powder for oral suspension": "pluhur për suspension oral",
    "powder for oral solution": "pluhur për solucion oral", "granules for oral suspension": "granula për suspension oral",
    "oral drops, solution": "pika orale", "oral drops solution": "pika orale", "cutaneous solution": "solucion për lëkurën",
    "lozenges": "pastila", "nasal spray, solution": "sprej për hundën", "nasal spray, suspension": "sprej për hundën",
    "nasal spray suspension": "sprej për hundën", "nasal drops, solution": "pika për hundën",
    "inhalation powder": "pluhur për inhalim", "pressurised inhalation, suspension": "inhalator",
    "effervescent granules": "granula shkumuese", "emulsion for infusion": "emulsion për infuzion",
    "suspension for injection": "suspension për injeksion",
}


# Për format që nuk janë te tabela: rregulla sipas fjalëve (radha ka rëndësi).
_RREGULLAT_E_FORMES = [
    (r"eye drop", "pika për sytë"), (r"ear drop", "pika për veshët"), (r"eye ointment|eye gel", "pomadë për sytë"),
    (r"nasal spray", "sprej për hundën"), (r"nasal", "pika për hundën"), (r"inhal|nebuli", "për inhalim"),
    (r"infusion", "solucion për infuzion"), (r"injection|injectable", "për injeksion"),
    (r"transdermal|patch", "ngjitës transdermal"), (r"vaginal", "për përdorim vaginal"),
    (r"suppositor", "supozitorë"), (r"lozenge|pastille", "pastila"), (r"syrup", "shurup"),
    (r"effervescent", "shkumuese"), (r"chewable", "tableta për t'u përtypur"),
    (r"orodispersible", "tableta që treten në gojë"), (r"(prolonged|modified|extended|sustained).?release", "me çlirim të zgjatur"),
    (r"gastro.?resistant|enteric", "gastrorezistente"), (r"film.?coated", "tableta të veshura me film"),
    (r"tablet", "tableta"), (r"capsul", "kapsula"), (r"granul", "granula"), (r"powder", "pluhur"),
    (r"suspension", "suspension"), (r"emulsion", "emulsion"), (r"oral drops|drops", "pika"),
    (r"solution", "solucion"), (r"cream", "krem"), (r"ointment", "pomadë"), (r"\bgel\b", "xhel"),
    (r"spray", "sprej"), (r"shampoo", "shampo"), (r"lotion", "losion"),
]


def forma_shqip(forma: str) -> str:
    f = " ".join((forma or "").replace(" - ", "-").split())
    if f.lower() in FORMAT:
        return FORMAT[f.lower()]
    pjeset = []
    for rr, sq in _RREGULLAT_E_FORMES:
        if re.search(rr, f, re.I) and not any(sq in p or p in sq for p in pjeset):
            pjeset.append(sq)
        if len(pjeset) == 2:
            break
    if not pjeset:
        return f
    baza = [p for p in pjeset if not p.startswith(("me ", "për ", "shkumuese", "gastro"))]
    mod = [p for p in pjeset if p not in baza]
    return " ".join((baza or ["tableta"]) + mod)


def _emri_kompanise(emri: str) -> str:
    """'BEECHAM GROUP PLC- MBRETËRI E BASHKUAR' → 'Beecham Group Plc (Mbretëri e Bashkuar)'."""
    emri, _, vendi = emri.rpartition("- ") if "- " in emri else (emri, "", "")
    t = lambda x: re.sub(r"\b(E|Dhe|Te|Të)\b", lambda m: m.group(1).lower(), x.strip().title())
    return t(emri) + (f" ({t(vendi)})" if vendi else "")


def _emri_lendes_shqip(emri: str) -> str:
    return " ".join(w.capitalize() if len(w) > 2 else w.lower() for w in emri.split())


def eshte_pa_recete(produktet: list[dict]) -> bool | None:
    """True = të gjitha në listën OTC, False = asnjë, None = të përziera."""
    v = {bool(p.get("pa_recete")) for p in produktet}
    return v.pop() if len(v) == 1 else None


def pergjigje(gjetja: dict, ka_simptoma: bool = False) -> str:
    produktet = gjetja["produktet"]
    otc = eshte_pa_recete(produktet)
    rr = []
    if gjetja["lloji"] == "emer":
        p0 = produktet[0]
        lendet = " + ".join(_emri_lendes_shqip(emri_i_lendes(l)) for l in (p0.get("lendet") or [p0["lenda_aktive"]]))
        rr.append(f"💊 **{p0['emri_tregtar'].title()}** është ilaç i autorizuar në Shqipëri (regjistri AKBPM).")
        rr.append(f"- **Lënda aktive:** {lendet}")
        format_ = list(dict.fromkeys(f"{forma_shqip(p['forma'])} {p['doza']}".strip() for p in produktet))
        rr.append(f"- **Format e autorizuara:** {'; '.join(format_[:MAKS_FORMA])}"
                  + (f" (dhe {len(format_) - MAKS_FORMA} të tjera)" if len(format_) > MAKS_FORMA else ""))
        if p0.get("mbajtesi"):
            rr.append(f"- **Mbajtësi i autorizimit:** {_emri_kompanise(p0['mbajtesi'])}")
    else:
        emri = _emri_lendes_shqip(gjetja["emri"])
        emrat = list(dict.fromkeys(p["emri_tregtar"].title() for p in produktet))
        rr.append(f"💊 **{emri}** është lëndë aktive e {len(produktet)} "
                  f"{'produkti' if len(produktet) == 1 else 'produkteve'} të autorizuara në Shqipëri (regjistri AKBPM).")
        rr.append(f"- **Emra tregtarë:** {', '.join(emrat[:8])}" + (f" (dhe {len(emrat) - 8} të tjerë)" if len(emrat) > 8 else ""))
        format_ = list(dict.fromkeys(forma_shqip(p["forma"]) for p in produktet))
        rr.append(f"- **Format:** {', '.join(format_[:MAKS_FORMA])}")
    rr.append("")
    if otc is False:
        rr.append("⛔ **Kërkon recetë mjekësore.** Nuk figuron në listën zyrtare të barnave pa recetë (Urdhri 501, "
                  "3.7.2018). Nuk mund ta sugjeroj dhe nuk jap doza: merre vetëm nëse ta ka përshkruar mjeku, "
                  "ashtu si ta ka shkruar ai.")
    elif otc is True:
        rr.append("✅ **Është në listën zyrtare të barnave pa recetë** (Urdhri 501, 3.7.2018). Dozën dhe "
                  "kohëzgjatjen merri nga fletëudhëzuesi i paketimit dhe nga farmacisti, sidomos nëse merr ilaçe të tjera.")
    else:
        pa = list(dict.fromkeys(p["emri_tregtar"].title() for p in produktet if p.get("pa_recete")))
        rr.append(f"⚠️ **Disa produkte janë pa recetë** ({', '.join(pa[:5])}), **të tjerat kërkojnë recetë.** "
                  "Mos merr asnjë pa e pyetur farmacistin ose mjekun; dozën e jep fletëudhëzuesi.")
    if ka_simptoma:
        rr.append("\nNëse ke simptoma, më trego çfarë ndjen dhe të them çfarë mund të marrësh pa recetë.")
    rr.append(f"\n_Burimi: Regjistri i barnave të autorizuara, AKBPM ({indeksi().get('shkarkuar') or 'akbpm.gov.al'}). "
              "Ky është vetëm informacion, jo këshillë mjekësore._")
    return "\n".join(rr)
