"""Shqipja e folur → shqip standard, që bota ta kuptojë mesazhin ashtu si e shkruajnë njerëzit.

    "po m dhem kryt e kom zjarrmi qe prej dje"  →  "po me dhemb koka e kam temperature prej dje"
    "s'po muj me marr frym"                      →  "nuk mund te marr fryme"

Të dhënat janë te data/fjalori_shqip.json (gegërisht, shkurtime chat-i, "q" në vend të "ç", gabime shkrimi).
Rezultati është i normalizuar (pa ë/ç, shkronja të vogla), njësoj si config.normalizo.
Mesazhi origjinal nuk humbet: kërkimi përdor të dy variantet.
"""
import json
import re
from functools import lru_cache

from config import ROOT, normalizo

SKEDARI = ROOT / "data" / "fjalori_shqip.json"


@lru_cache
def _fjalori():
    d = json.loads(SKEDARI.read_text(encoding="utf-8"))
    fjale = {}
    for grupi in d["fjale"].values():
        fjale.update({k: v for k, v in grupi.items() if k != v})
    # Më të gjatat të parat: "kom qen" para "kom".
    alternativat = "|".join(sorted(map(re.escape, fjale), key=len, reverse=True))
    return {
        "para": [(re.compile(p), z) for p, z in d["shprehje_para"]],
        "pas": [(re.compile(p), z) for p, z in d["shprehje_pas"]],
        "fjale": fjale,
        "pattern": re.compile(rf"(?<![\w'])({alternativat})(?![\w'])"),
    }


def standardizo(tekst: str) -> str:
    """Kthen variantin standard (i normalizuar) të mesazhit. Mesazhi në anglisht kthehet në shqip."""
    if gjuha_e_mesazhit(tekst) == "en":
        return anglisht_ne_shqip(tekst)
    f = _fjalori()
    t = normalizo(tekst)
    for p, z in f["para"]:
        t = p.sub(z, t)
    t = f["pattern"].sub(lambda m: f["fjale"][m.group(1)], t)
    for p, z in f["pas"]:
        t = p.sub(z, t)
    return " ".join(t.split())


def varianta(tekst: str) -> list[str]:
    """Mesazhi i normalizuar dhe varianti standard (pa dublikata)."""
    return list(dict.fromkeys([normalizo(tekst), standardizo(tekst)]))


def ndryshimet(tekst: str) -> list[tuple[str, str]]:
    """Fjalët që u kuptuan ndryshe, p.sh. [("kryt", "koka"), ("zjarrmi", "temperature")]. Për t'ia treguar personit."""
    origjinal, standard = normalizo(tekst).split(), standardizo(tekst).split()
    if origjinal == standard:
        return []
    import difflib
    dalja = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=origjinal, b=standard).get_opcodes():
        if op != "equal":
            a, b = " ".join(origjinal[i1:i2]), " ".join(standard[j1:j2])
            if a and b:
                dalja.append((a, b))
    return dalja


# ---------------------------------------------------------------- anglisht
SKEDARI_EN = ROOT / "data" / "fjalori_anglisht.json"
_SHENJE = "\x00"  # rrethon pjesët e përkthyera, që të mos preken më


@lru_cache
def _fjalori_en():
    d = json.loads(SKEDARI_EN.read_text(encoding="utf-8"))
    neutrale = set(d["fjale_neutrale"])
    f = _fjalori()
    shqip = {w for k, v in f["fjale"].items() for w in (k + " " + v).split()}
    shqip |= {"kam", "jam", "dhemb", "nuk", "eshte", "cfare", "dhe", "qe", "nje", "mund", "duhet", "ilac", "ilace",
              "koka", "barku", "fyti", "temperature", "shume", "edhe", "tani", "dite", "prej", "marr", "si", "jo",
              "faleminderit", "pershendetje", "mirupafshim", "ka", "kemi", "me", "dhimbje", "kolle", "grip"}
    return {"en": set(d["fjale_angleze"]) - neutrale, "sq": shqip - neutrale - set(d["fjale_angleze"]),
            "shprehje": [(re.compile(p), z) for p, z in d["shprehje"]], "pastro": set(d["fjale_angleze"])}


def gjuha_e_mesazhit(tekst: str) -> str:
    """'en' ose 'sq'. E kujdesshme: në dyshim kthen 'sq' (shumica e mesazheve janë shqip)."""
    if re.search(r"[ëçËÇ]", tekst or ""):
        return "sq"
    f = _fjalori_en()
    fjalet = re.findall(r"[a-z']+", (tekst or "").lower())
    en = sum(w in f["en"] for w in fjalet)
    sq = sum(normalizo(w) in f["sq"] for w in fjalet)
    if en >= 2 and en > 2 * sq:
        return "en"
    if en == 1 and sq == 0 and len(fjalet) <= 2:
        return "en"
    return "sq"


def anglisht_ne_shqip(tekst: str) -> str:
    """'I have a headache since yesterday' → 'kam me dhemb koka prej dje' (shqip i normalizuar).
    Fjalët angleze që mbeten pa përkthim hiqen; emrat e ilaçeve dhe numrat mbeten."""
    f = _fjalori_en()
    t = " " + " ".join((tekst or "").lower().replace("’", "'").split()) + " "
    for p, z in f["shprehje"]:
        t = p.sub(lambda m: f" {_SHENJE}{m.expand(z)}{_SHENJE} ", t)
    pjeset = t.split(_SHENJE)
    dalja = []
    for i, pjese in enumerate(pjeset):
        if i % 2:  # e përkthyer
            dalja.append(pjese)
        else:
            dalja += [w for w in re.findall(r"[\w']+|\?", pjese) if w not in f["pastro"]]
    return " ".join(normalizo(" ".join(dalja)).split())


def ka_shqip(tekst: str) -> bool:
    """A ka mesazhi të paktën një shenjë shqipeje (ë/ç ose një fjalë shqipe e njohur)."""
    if re.search(r"[ëçËÇ]", tekst or ""):
        return True
    f = _fjalori_en()
    return any(normalizo(w) in f["sq"] for w in re.findall(r"[a-z']+", (tekst or "").lower()))
