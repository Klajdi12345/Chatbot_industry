"""Shkarkon datasetet e mëdha mjekësore (publike, falas) në data/burime/:

  1. MedlinePlus Health Topics (U.S. National Library of Medicine): ~1000 tema shëndetësore në anglisht
     (simptoma, sëmundje, kur duhet mjeku). Skedari XML i plotë, përditësohet çdo ditë.
  2. openFDA Drug Labels (U.S. FDA): fletëudhëzuesit zyrtarë të ilaçeve të bazës (indikacionet,
     paralajmërimet, "mos e përdor nëse", "pyet mjekun nëse", shtatzënia, dozimi).

Të dhënat janë në anglisht; bge-m3 i kërkon edhe me pyetje shqip, dhe modeli i përmbledh në gjuhën e personit.
Dozat që sheh personi vijnë GJITHMONË nga data/njohurite.json, jo nga këto burime (janë për SHBA-në).

Ekzekuto:  python shkarko_datasetet.py      pastaj:  python ngarko_burimet.py
"""
import json
import re
import time

import requests

from config import ROOT

DOSJA = ROOT / "data" / "burime"
MEDLINEPLUS_FAQJA = "https://medlineplus.gov/xml.html"
OPENFDA = "https://api.fda.gov/drug/label.json"
KOKA = {"User-Agent": "FarmaBot/1.0 (local pharmacy assistant)"}

# id e ilaçit në bazë → emri gjenerik në openFDA (None = nuk ka fletëudhëzues amerikan për të)
EMRAT_OPENFDA = {
    "paracetamol": "acetaminophen", "ibuprofen": "ibuprofen", "aspirine": "aspirin", "loratadine": "loratadine",
    "cetirizine": "cetirizine", "oksimetazoline": "oxymetazoline", "kripe_fiziologjike": "sodium chloride",
    "antacid": "aluminum hydroxide", "omeprazol": "omeprazole", "loperamid": "loperamide", "ors": None,
    "dekstrometorfan": "dextromethorphan", "ambroksol": None, "makrogol": "polyethylene glycol 3350",
    "simetikone": "simethicone", "butilskopolamine": None, "pastile_fyti": None,
    "hidrokortizon_krem": "hydrocortisone", "klotrimazol_krem": "clotrimazole", "diklofenak_xhel": "diclofenac",
    "naproksen": "naproxen", "desloratadine": "desloratadine", "feksofenadine": "fexofenadine",
    "famotidine": "famotidine", "alginat": None, "bisakodil": "bisacodyl", "laktuloze": "lactulose",
    "racekadotril": None, "dimenhidrinat": "dimenhydrinate", "difenhidramine": "diphenhydramine",
    "melatonine": None, "valeriane": None, "benzokaine_xhel": "benzocaine",
    "klorheksidine_shpelares": "chlorhexidine gluconate", "aciklovir_krem": "acyclovir",
    "krem_hemorroidesh": "lidocaine", "lot_artificiale": "hypromellose", "kromoglikat_pika": "cromolyn",
    "benzoil_peroksid": "benzoyl peroxide", "dekspantenol_krem": "dexpanthenol", "povidon_jod": "povidone-iodine",
    "dimetikon_losion": "dimethicone", "ketokonazol_shampo": "ketoconazole", "klotrimazol_vaginal": "clotrimazole",
    "mebendazol": "mebendazole", "nikotine": "nicotine", "krem_emolient": None, "acid_salicilik": "salicylic acid",
    "amorolfine": None, "terbinafine_krem": "terbinafine", "benzidamine_sprej": None,
    "acetilcisteine": "acetylcysteine", "hedera_shurup": None, "mentol_balsam": "menthol",
    "vitamine_d": None, "vitamine_c": None, "zink": None, "multivitamine": None, "hekur": "ferrous sulfate",
    "acid_folik": "folic acid", "magnez": "magnesium citrate", "probiotik": None,
    "glicerine_supozitor": "glycerin", "senna": "sennosides", "oksid_zinku_krem": "zinc oxide",
    "permetrine_krem": "permethrin", "heparinoid_xhel": None, "aloe_xhel": None, "repelent": None,
    "pika_veshi_dylle": "carbamide peroxide", "plaster_hidrokoloid": None, "klorur_alumini": "aluminum chloride",
    "minoksidil": "minoxidil", "vazeline": "petrolatum",
}

SEKSIONET = ["purpose", "indications_and_usage", "do_not_use", "ask_doctor", "ask_doctor_or_pharmacist",
             "when_using", "stop_use", "pregnancy_or_breast_feeding", "keep_out_of_reach_of_children",
             "warnings", "dosage_and_administration", "contraindications", "warnings_and_cautions",
             "adverse_reactions", "drug_interactions", "use_in_specific_populations"]


def shkarko_medlineplus():
    faqja = requests.get(MEDLINEPLUS_FAQJA, headers=KOKA, timeout=60).text
    lidhjet = sorted(set(re.findall(r"https://medlineplus\.gov/xml/mplus_topics_[\d-]+\.xml", faqja)))
    if not lidhjet:
        raise RuntimeError("Nuk u gjet skedari XML te faqja e MedlinePlus.")
    url = lidhjet[-1]
    print(f"MedlinePlus: {url}")
    r = requests.get(url, headers=KOKA, timeout=300)
    r.raise_for_status()
    (DOSJA / "medlineplus_topics.xml").write_bytes(r.content)
    print(f"  ✓ {len(r.content) / 1e6:.1f} MB")


def _etiketa_me_e_plote(emri: str) -> dict | None:
    """Fletëudhëzuesi me më shumë seksione (OTC i pari, pastaj me recetë)."""
    for filtri in (' AND openfda.product_type:"HUMAN OTC DRUG"', ""):
        r = requests.get(OPENFDA, headers=KOKA, timeout=60,
                         params={"search": f'openfda.generic_name:"{emri}"{filtri}', "limit": 10})
        if r.status_code == 404:
            continue
        r.raise_for_status()
        rezultatet = r.json().get("results") or []
        if rezultatet:
            return max(rezultatet, key=lambda x: sum(1 for s in SEKSIONET if x.get(s)))
    return None


def shkarko_openfda():
    dalja = {}
    for bid, emri in EMRAT_OPENFDA.items():
        if not emri:
            continue
        try:
            etiketa = _etiketa_me_e_plote(emri)
        except requests.RequestException as e:
            print(f"  ! {bid}: {e}")
            continue
        if not etiketa:
            print(f"  - {bid} ({emri}): s'ka fletëudhëzues")
            continue
        dalja[bid] = {"emri": emri, "set_id": etiketa.get("set_id"),
                      "lloji": (etiketa.get("openfda") or {}).get("product_type", [""])[0],
                      "seksionet": {s: " ".join(etiketa[s]) for s in SEKSIONET if etiketa.get(s)}}
        print(f"  ✓ {bid} ({emri}): {len(dalja[bid]['seksionet'])} seksione")
        time.sleep(0.3)  # openFDA lejon ~240 kërkesa/minutë pa çelës
    (DOSJA / "openfda_labels.json").write_text(json.dumps(dalja, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"openFDA: {len(dalja)} ilaçe")


def main():
    DOSJA.mkdir(parents=True, exist_ok=True)
    shkarko_medlineplus()
    shkarko_openfda()


if __name__ == "__main__":
    main()
