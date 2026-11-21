"""Fjalori i shqipes së folur (gjuha.py + data/fjalori_shqip.json) dhe mënyra si bota i kupton mesazhet
në gegërisht / chat. Pjesa e parë punon pa shërbime; pjesa e dytë kërkon Neo4j + Ollama (bge-m3)."""
import json
import re

import pytest

from config import ROOT, normalizo
from gjuha import ndryshimet, standardizo

FJALORI = json.loads((ROOT / "data" / "fjalori_shqip.json").read_text(encoding="utf-8"))


def test_celesat_jane_te_normalizuar():
    for grupi, fjale in FJALORI["fjale"].items():
        for k, v in fjale.items():
            assert k == normalizo(k), f"{grupi}: çelësi '{k}' duhet të jetë pa ë/ç dhe me shkronja të vogla"
            assert v == normalizo(v), f"{grupi}: vlera '{v}' duhet të jetë e normalizuar"


def test_shprehjet_kompilohen():
    for p, z in FJALORI["shprehje_para"] + FJALORI["shprehje_pas"]:
        re.compile(p).sub(z, "prove")


@pytest.mark.parametrize("tekst, pritet", [
    ("po m dhem kryt", "po me dhemb koka"),
    ("kom zjarrmi qe prej dje", "kam temperature prej dje"),
    ("s'po muj me marr frym", "nuk mund te marr fryme"),
    ("m'dhemb dhâmbi", "me dhemb dhembi"),
    ("cuni 5 vjeç ka diare", "djali 5 vjec ka diarre"),
    ("kam sheqer", "kam diabet"),
    ("jam me barre", "jam shtatzene"),
    ("s'kam diabet", "nuk kam diabet"),
    ("kam dhimbje ne kraharor", "kam dhimbje ne gjoks"),
    ("sa hapa ne dite", "sa tableta ne dite"),
    ("barku m shkon", "me shkon barku"),
    ("s'po muj me fjet hiq", "nuk fle dot fare"),
    ("m djeg lukthi", "me djeg stomaku"),
])
def test_standardizo(tekst, pritet):
    assert standardizo(tekst) == pritet


@pytest.mark.parametrize("tekst", ["më dhemb koka", "kam temperaturë", "si t'i marr?", "sa herë ta marr?",
                                   "faleminderit", "a mund ta marr me bark bosh?"])
def test_shqipja_standarde_nuk_ndryshon(tekst):
    assert standardizo(tekst) == normalizo(tekst)
    assert ndryshimet(tekst) == []


@pytest.mark.parametrize("tekst", [
    "m dhem kraharori fort",            # dhimbje gjoksi
    "s'po muj me marr frym",            # vështirësi në frymëmarrje
    "mu fik nana",                      # humbje ndjenjash
])
def test_urgjencat_gegerisht(tekst):
    from chatbot import kontrollo_urgjencen
    assert kontrollo_urgjencen(tekst)


@pytest.mark.parametrize("tekst, gjendja", [("jom shtatzan", "shtatzeni"), ("kam sheqer", "diabet"),
                                            ("kam presion t lart", "hipertension")])
def test_profili_gegerisht(tekst, gjendja):
    from chatbot import lexo_profilin_nga_teksti
    assert gjendja in lexo_profilin_nga_teksti(tekst)[0]


def test_mohimi_me_shkurtim():
    from chatbot import lexo_profilin_nga_teksti
    assert "diabet" not in lexo_profilin_nga_teksti("s'kam sheqer")[0]


@pytest.mark.sherbime
@pytest.mark.parametrize("tekst, pritet", [
    ("po m dhem kryt", "dhimbje_koke"), ("kom zjarrmi", "temperature"), ("m dhem gurmazi", "dhimbje_fyti"),
    ("m dhem kurrizi", "dhimbje_shpine"), ("m shkon barku", "diarre"), ("m djeg lukthi", "urth"),
    ("s'po muj me fjet hiq", "pagjumesi"), ("jom ftof keq", "grip_ftohje"), ("m dhem dhambi", "dhimbje_dhembi"),
    ("kom koll me glbaz", "kolle_gelbaze"), ("m ha lkura", "kruajtje_lekure"), ("m vjen me vjell", "nauze_te_vjella"),
    ("m merren mendt", "marramendje"), ("m dalin puqrra", "akne"), ("m djeg kur shurrej", "cistit"),
])
def test_simptomat_gegerisht(tekst, pritet):
    from chatbot import kerko_simptomat
    gjetur, _ = kerko_simptomat(tekst)
    assert pritet in [s["id"] for s in gjetur], (tekst, [s["id"] for s in gjetur])


@pytest.mark.llm
def test_mendimi_i_thelle_kupton_dhe_tregon_hapat():
    from chatbot import Profili, pergjigju
    hapat = []
    p = pergjigju("m ka zan ni dhimje te lukthi kur ha", [], Profili(mosha=30), mendo=True, on_hap=hapat.append)
    assert p.simptomat, p.hapat
    assert hapat == p.hapat and any("Mendo" in h or "mendoj" in h for h in hapat)
    assert p.kuptimi


@pytest.mark.llm
def test_urgjenca_nuk_pret_mendimin():
    from chatbot import Profili, pergjigju
    p = pergjigju("s'po muj me marr frym", [], Profili(), mendo=True)
    assert p.urgjence and p.sekonda < 5 and not p.mendimi_modelit
