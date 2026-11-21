"""Integriteti i bazës së njohurive (data/njohurite.json). Nuk kërkon shërbime."""
import re

import pytest

FUSHAT_BARNA = ["id", "emer", "lende_aktive", "forma", "emra_tregtare", "doza", "doza_maks", "kohezgjatja",
                "si_merret", "paralajmerime", "efekte_anesore", "kunderindikime", "kujdes"]
FUSHAT_SIMPTOMA = ["id", "emer", "pershkrim", "info", "fraza", "barnat", "shenja_alarmi", "keshilla", "fjale_kyce"]


def test_madhesia_e_datasetit(njohurite):
    assert len(njohurite["barnat"]) >= 70
    assert len(njohurite["simptomat"]) >= 60
    assert len(njohurite["gjendjet"]) >= 25
    assert sum(len(s["fraza"]) for s in njohurite["simptomat"]) >= 600


@pytest.mark.parametrize("celesi", ["barnat", "simptomat", "gjendjet"])
def test_id_unike(njohurite, celesi):
    ids = [x["id"] for x in njohurite[celesi]]
    assert len(ids) == len(set(ids)), f"id të përsëritura te {celesi}"


def test_barnat_kane_te_gjitha_fushat(njohurite):
    for b in njohurite["barnat"]:
        mungojne = [f for f in FUSHAT_BARNA if f not in b]
        assert not mungojne, f"{b['id']}: mungojnë {mungojne}"
        for f in ("emer", "lende_aktive", "doza", "doza_maks", "kohezgjatja", "si_merret"):
            assert b[f].strip(), f"{b['id']}.{f} është bosh"
        assert b["emra_tregtare"], f"{b['id']}: pa emra tregtarë"


def test_simptomat_kane_te_gjitha_fushat(njohurite):
    for s in njohurite["simptomat"]:
        mungojne = [f for f in FUSHAT_SIMPTOMA if f not in s]
        assert not mungojne, f"{s['id']}: mungojnë {mungojne}"
        assert s["info"].strip(), f"{s['id']}: pa info"
        assert len(s["fraza"]) >= 4, f"{s['id']}: shumë pak fraza"
        assert len(s["shenja_alarmi"]) >= 2, f"{s['id']}: duhen të paktën 2 shenja alarmi"


def test_referencat_ekzistojne(njohurite):
    barnat = {b["id"] for b in njohurite["barnat"]}
    gjendjet = {g["id"] for g in njohurite["gjendjet"]}
    for s in njohurite["simptomat"]:
        for bid in s["barnat"]:
            assert bid in barnat, f"{s['id']} → barna e panjohur {bid}"
    for b in njohurite["barnat"]:
        for k in ("kunderindikime", "kujdes"):
            for g in b[k]:
                assert g in gjendjet, f"{b['id']}.{k} → gjendje e panjohur {g}"


def test_cdo_bar_perdoret_nga_nje_simptome(njohurite):
    te_perdorura = {bid for s in njohurite["simptomat"] for bid in s["barnat"]}
    pa_perdorim = [b["id"] for b in njohurite["barnat"] if b["id"] not in te_perdorura]
    assert not pa_perdorim, f"barna që s'lidhen me asnjë simptomë: {pa_perdorim}"


def test_fjalet_kyce_kompilohen_dhe_kapin_frazat(njohurite):
    from config import normalizo
    for s in njohurite["simptomat"]:
        pattern = re.compile(s["fjale_kyce"])
        kapur = [f for f in s["fraza"] if pattern.search(normalizo(f))]
        assert kapur, f"{s['id']}: fjalët kyçe nuk kapin asnjë nga frazat e veta"


def test_fjalet_kyce_jane_te_normalizuara(njohurite):
    """Teksti krahasohet pa ë/ç: një fjalë kyçe me ë ose ç nuk do të kapte kurrë asgjë."""
    for s in njohurite["simptomat"]:
        assert not re.search(r"[ëçËÇA-Z]", s["fjale_kyce"]), f"{s['id']}: fjalë kyçe me ë/ç ose shkronja të mëdha"


@pytest.mark.parametrize("bid,gjendja", [
    ("ibuprofen", "shtatzeni"), ("ibuprofen", "ulcer"), ("ibuprofen", "antikoagulante"),
    ("naproksen", "shtatzeni"), ("naproksen", "ulcer"), ("aspirine", "nen_16"),
    ("dekstrometorfan", "antidepresive"), ("difenhidramine", "glaukome"), ("difenhidramine", "prostate"),
    ("difenhidramine", "mbi_65"), ("melatonine", "shtatzeni"), ("loperamid", "femije_nen_12"),
    ("benzokaine_xhel", "nen_2"), ("povidon_jod", "tiroide"), ("acid_salicilik", "diabet"),
    ("mebendazol", "shtatzeni"), ("racekadotril", "shtatzeni"), ("dimenhidrinat", "glaukome"),
    ("minoksidil", "shtatzeni"), ("minoksidil", "gjidhenie"), ("magnez", "veshka"), ("mentol_balsam", "nen_2"),
    ("senna", "femije_nen_12"), ("probiotik", "imunitet"), ("acetilcisteine", "nen_2"), ("hedera_shurup", "nen_2"),
])
def test_kunderindikimet_kritike(njohurite, bid, gjendja):
    """Rregulla sigurie që nuk duhet të humbasin kurrë gjatë ndryshimeve të të dhënave."""
    b = next(b for b in njohurite["barnat"] if b["id"] == bid)
    assert gjendja in b["kunderindikime"], f"{bid} duhet të jetë i kundërindikuar për {gjendja}"


def test_pa_doze_pediatrike_te_barnat(njohurite):
    """Dozat në databazë janë për të rritur; për fëmijë aplikacioni nuk shfaq doza."""
    for b in njohurite["barnat"]:
        assert "fëmij" not in b["doza"].lower() or "pediatr" in b["doza"].lower(), b["id"]
