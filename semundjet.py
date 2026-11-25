"""Sëmundjet dhe thyerjet (data/semundjet.json) për FarmaBot-in: VETËM INFORMACION.

    from semundjet import gjej, pergjigje
    gjetjet = gjej("si trajtohet hipertensioni?")   → [hyrja, ...] (më të përshtatshmet)
    pergjigje(gjetjet, "si trajtohet hipertensioni?") → tekst markdown shqip

Kërkimi bëhet pa model gjuhësor: emri shqip, emrat në kllapa, emri anglisht dhe disa emra të folur
(EMRA_TE_FOLUR) kthehen në rrënjë fjalësh; një hyrje gjendet kur të gjitha rrënjët dalluese janë te mesazhi.
Trajtimet me recetë përshkruhen si "vendos mjeku": FarmaBot-i nuk sugjeron kurrë ilaç me recetë.
"""
import json
import re
from functools import lru_cache

from config import ROOT, normalizo

SKEDARI = ROOT / "data" / "semundjet.json"
# Fjalë që nuk e dallojnë një hyrje nga tjetra (por mund të ndihmojnë si bonus).
TE_PERGJITHSHME = {"semundja", "semundje", "kronike", "kronik", "pjeses", "pjesa", "siperme", "poshtme", "trupit",
                   "tip", "arterial", "arteriale", "disorder", "disease", "chronic", "unspecified", "without",
                   "pathological", "fracture", "thyerje", "thyerja", "kockes", "kockave", "kocka", "both", "shafts",
                   "shaft", "and", "dhe", "the", "of", "with", "primary", "essential", "mellitus", "rekurent",
                   "rekurente", "ose", "the", "lartë", "larte", "i", "e", "te", "se", "ne", "me", "per", "nga"}
THYERJE = r"thy|fraktur|fracture|kris|broke"
# Si i quajnë njerëzit (përveç emrit zyrtar). Çelësi = id te semundjet.json.
EMRA_TE_FOLUR = {
    "diabeti_tip2": ["sheqer ne gjak tip 2", "diabet tip 2", "diabet 2"],
    "diabeti_tip1": ["diabet tip 1", "diabet 1", "diabet insulinovarur"],
    "hipertensioni": ["tension i larte", "tensioni", "presion i larte", "hipertension", "high blood pressure"],
    "semundja_ishemike_kronike": ["ishemi e zemres", "angine", "angina", "semundje koronare", "arteriet koronare",
                                  "coronary"],  # jo "koronare" vetëm: "jam me korona" = COVID
    "deshtimi_zemres": ["insuficience kardiake", "insuficienca e zemres", "heart failure"],
    "fibrilacioni_atrial": ["fibrilacion", "aritmi", "ritem i crregullt", "afib"],
    "astma": ["astme", "asthma"],
    "semundja_pulmonare_obstruktive": ["spok", "copd", "bronkit kronik", "emfizem"],
    "osteoartriti_gjurit": ["artroze", "gonartroze", "artrit i gjurit", "knee arthritis"],
    "artriti_reumatoid": ["reumatoid", "rheumatoid"],
    "osteoporoza": ["osteoporoz", "kocka te dobeta"],
    "hipotiroidizmi": ["hipotiroid", "tiroide e ulet", "tiroide qe punon pak", "hashimoto"],
    "semundja_kronike_veshkave": ["insuficience renale", "veshka kronike", "kidney disease"],
    "podagra": ["podager", "cerme", "gout", "acid urik"],
    "hiperlipidemia": ["kolesterol", "yndyra ne gjak", "hiperlipidemi", "cholesterol"],
    "obeziteti": ["obezitet", "mbipesh", "obesity"],
    "depresioni_rekurent": ["depresion", "depression"],
    "epilepsia": ["epileps", "kriza epileptike", "epilepsy"],
    "refluksi_gastroezofageal": ["refluks", "gerd", "reflux"],
    "migrena": ["migren", "migraine"],
    "thyerje_bimaleolare": ["kyci i kembes", "nyja e kembes", "ankle"],
    "thyerje_radiusi_distal": ["kyci i dores", "wrist"],
    "thyerje_qafa_femurit": ["ijes", "hip"],
    "thyerje_pertrokanterike": ["ijes", "hip"],
    "thyerje_klavikule": ["collarbone"],
    "thyerje_pateles": ["kupa e gjurit", "kneecap"],
}
INFO = (r"cfare (eshte|jane|do te thote)|c'?eshte|ceshte|me (trego|shpjego)|informacion|"
        r"si (trajtohet|sherohet|kurohet|diagnostikohet|parandalohet|shfaqet|ndodh|kuptohet|zbulohet)|"
        r"sa (kohe )?(zgjat|kerkon|vazhdon|do)|a (sherohet|kurohet|eshte e rrezikshme|eshte serioz)|"
        r"\b(simptomat|shenjat|shkaqet|shkaktaret|komplikimet|trajtimi|kurimi|sherimi|parandalimi|diagnoza|"
        r"faktoret)\b|what is|what are|symptoms of|signs of|treatment|how long|causes of|tell me about")
SEKSIONET = [  # (pattern, fusha, titulli)
    (r"simptom|shenj|si (shfaqet|kuptohet)|symptom|signs", "simptomat", "Simptomat"),
    (r"shkak|pse (ndodh|vjen)|nga vjen|cause|faktor|rrezik", "shkaqet", "Shkaqet"),
    (r"diagnoz|si (diagnostikohet|zbulohet)|analiz|diagnos", "diagnoza", "Si diagnostikohet"),
    (r"trajt|kur|ilac|bar|terapi|treat|operacion|kirurg", "trajtimi", "Si trajtohet"),
    (r"sa (kohe )?(zgjat|kerkon|vazhdon|do)|sherohet|sherim|how long|recover", "koha_e_sherimit", "Koha e shërimit"),
    (r"komplikim|complicat", "komplikimet", "Komplikimet"),
    (r"parandal|shmang|prevent", "parandalimi", "Parandalimi"),
]


def _rrenja(f: str) -> str:
    """Rrënja e fjalës pa mbaresat shqipe: 'klavikulës' → 'klavikul', 'kyçin' → 'kyci', 'dorës' → 'dore'."""
    if f.isdigit() or len(f) < 4:
        return f
    return f[:max(5, len(f) - 2)] if len(f) > 5 else f[:4]


def _fjalet(tekst: str) -> list[str]:
    return [f for f in re.split(r"[^a-z0-9]+", normalizo(tekst)) if f]


def _rrenjet_dalluese(alias: str) -> tuple[str, ...]:
    return tuple(_rrenja(f) for f in _fjalet(alias) if f not in TE_PERGJITHSHME and (len(f) >= 3 or f.isdigit()))


@lru_cache
def hyrjet() -> list[dict]:
    rows = json.loads(SKEDARI.read_text(encoding="utf-8"))["hyrjet"]
    for h in rows:
        emri = h["emri_shqip"]
        aliaset = [re.sub(r"\([^)]*\)", " ", emri), *re.findall(r"\(([^)]*)\)", emri),
                   re.sub(r"\([^)]*\)", " ", h["emri_anglisht"]), *EMRA_TE_FOLUR.get(h["id"], [])]
        aliaset = [a for x in aliaset for a in re.split(r"\s*/\s*|,\s*", x) if a.strip()]
        h["_rrenjet"] = [r for r in dict.fromkeys(_rrenjet_dalluese(a) for a in aliaset) if r]
        # Të gjitha fjalët e emrit (edhe "trupit", "sipërme"): dallojnë hyrjet e ngjashme si bonus.
        h["_bonus"] = {_rrenja(f) for f in _fjalet(emri + " " + h["emri_anglisht"]) if len(f) >= 4}
    return rows


def _ka(fjalet: list[str], rrenja: str) -> bool:
    if rrenja.isdigit():
        return rrenja in fjalet
    return any(f.startswith(rrenja) for f in fjalet)


def gjej(tekst: str, variantet: list[str] | None = None) -> list[dict]:
    """Hyrjet që i përshtaten më mirë tekstit (zakonisht një; disa kur emri është i përgjithshëm, p.sh. 'diabeti')."""
    fjalet = [f for t in dict.fromkeys([tekst, *(variantet or [])]) for f in _fjalet(t)]
    thyerje = bool(re.search(THYERJE, " ".join(fjalet)))
    pikët = []
    for h in hyrjet():
        if h["kategoria"] == "thyerje" and not thyerje:
            continue
        me_e_mira = 0
        for rr in h["_rrenjet"]:
            fjale_te_kapura = [x for x in rr if _ka(fjalet, x)]
            # Të gjitha rrënjët e emrit (përveç shifrave që mungojnë: "diabeti" kap edhe tip 1 edhe tip 2).
            if all(_ka(fjalet, x) or x.isdigit() for x in rr) and any(not x.isdigit() for x in rr):
                me_e_mira = max(me_e_mira, sum(len(x) for x in fjale_te_kapura))
        if me_e_mira:
            pikët.append((me_e_mira + sum(_ka(fjalet, b) for b in h["_bonus"]), h))
    if not pikët:
        return []
    maks = max(p for p, _ in pikët)
    return [h for p, h in pikët if p == maks]


def eshte_pyetje_info(tekst: str) -> bool:
    return bool(re.search(INFO, normalizo(tekst)))


def _lista(x: list[str], n: int = 6) -> str:
    return "\n".join(f"- {e[0].upper() + e[1:]}" for e in x[:n])


def _koha(h: dict) -> str:
    k = h.get("koha_e_sherimit") or {}
    if k.get("min") is None:
        return (k.get("shenim") or "Sëmundje kronike: kontrollohet me trajtim afatgjatë.").replace("kronike:", "Kronike:")
    return f"Zakonisht {k['min']}–{k['max']} javë (varet nga rasti dhe trajtimi)."


def _seksioni(h: dict, fusha: str) -> str:
    if fusha == "trajtimi":
        rr = []
        if h.get("trajtimi_konservativ"):
            rr += ["**Pa operacion:**", _lista(h["trajtimi_konservativ"])]
        if h.get("trajtimi_kirurgjik"):
            rr += ["**Me operacion (kur duhet):**", _lista(h["trajtimi_kirurgjik"])]
        rr.append("_Trajtimin dhe çdo ilaç me recetë i vendos mjeku pas vizitës. Mos fillo dhe mos ndalo ilaçe vetë._")
        return "\n".join(rr)
    if fusha == "koha_e_sherimit":
        return _koha(h)
    if fusha == "shkaqet":
        return _lista(h["shkaqet"]) + ("\n\n**Faktorët e rrezikut:**\n" + _lista(h["faktoret_e_rrezikut"])
                                       if h.get("faktoret_e_rrezikut") else "")
    return _lista(h.get(fusha) or [])


def _urgjente(h: dict) -> str:
    if not h.get("shenjat_urgjente"):
        return ""
    return ("\n\n🚨 **Shko menjëherë në urgjencë ose telefono 127/112 nëse:**\n" + _lista(h["shenjat_urgjente"], 5))


def pergjigje(gjetjet: list[dict], tekst: str = "") -> str:
    t = normalizo(tekst)
    if len(gjetjet) > 1:
        rr = ["Kam informacion për disa sëmundje me këtë emër:"]
        rr += [f"- **{h['emri_shqip']}**: {h['pershkrimi']}" for h in gjetjet[:5]]
        rr.append("\nMë thuaj për cilën e ke fjalën (p.sh. *\"simptomat e " + gjetjet[0]["emri_shqip"].lower()
                  + "\"*) dhe të tregoj simptomat, trajtimin dhe kohën e shërimit.")
        return "\n".join(rr)
    h = gjetjet[0]
    kerkuar = [(fusha, titulli) for p, fusha, titulli in SEKSIONET if re.search(p, t)]
    rr = [f"🩺 **{h['emri_shqip']}** ({h['emri_anglisht']}, ICD-10 {h['kodi_icd10']})", "", h["pershkrimi"], ""]
    if not kerkuar:  # pyetje e përgjithshme: pak nga secila
        kerkuar = [("simptomat", "Simptomat"), ("trajtimi", "Si trajtohet"), ("koha_e_sherimit", "Koha e shërimit")]
    for fusha, titulli in kerkuar[:3]:
        rr += [f"**{titulli}:**", _seksioni(h, fusha), ""]
    rr.append(_urgjente(h).strip())
    rr.append(f"\n_Burimi: {h['burimi']}. Ky është vetëm informacion: për diagnozë dhe trajtim shko te mjeku._")
    rr.append("\nMund të më pyesësh edhe për *shkaqet*, *diagnozën*, *komplikimet* ose *parandalimin*.")
    return "\n".join(x for x in rr if x is not None)
