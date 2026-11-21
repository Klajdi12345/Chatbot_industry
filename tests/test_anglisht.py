"""Anglishtja: zbulimi i gjuhës, kthimi në shqip për logjikën, urgjencat me tekst fiks, kontrolli i numrave
te përkthimi. Pjesa e parë pa shërbime; kërkimi kërkon Neo4j + Ollama; përkthimi real është te -m llm."""
import pytest

from gjuha import anglisht_ne_shqip, gjuha_e_mesazhit, ka_shqip
from perkthimi import numrat_perputhen


@pytest.mark.parametrize("tekst", ["I have a headache", "my stomach hurts after eating", "how often should I take it?",
                                   "I am pregnant, can I take ibuprofen?", "I can't breathe", "headache", "thanks"])
def test_zbulohet_anglishtja(tekst):
    assert gjuha_e_mesazhit(tekst) == "en"


@pytest.mark.parametrize("tekst", ["më dhemb koka", "po m dhem kryt", "kam temperaturë", "sa here ta marr?",
                                   "a mund ta marr me bark bosh?", "faleminderit", "ok", "kam diarre", "jom ftof keq",
                                   "i kam dhene ilacin femijes", "do te shkoj te mjeku"])
def test_shqipja_nuk_ngatërrohet_me_anglishten(tekst):
    assert gjuha_e_mesazhit(tekst) == "sq"


@pytest.mark.parametrize("tekst, pritet", [
    ("I have a headache since yesterday", "me dhemb koka"),
    ("I am pregnant", "jam shtatzene"),
    ("my son is 5 years old", "5 vjec"),
    ("I have diarrhea for 2 days", "diarre"),
    ("how often should I take it?", "sa here"),
    ("something else?", "ilac tjeter"),
])
def test_anglisht_ne_shqip(tekst, pritet):
    assert pritet in anglisht_ne_shqip(tekst)


def test_mesazhet_neutrale_nuk_kane_shqip():
    assert not ka_shqip("ok") and not ka_shqip("2") and ka_shqip("faleminderit")


@pytest.mark.parametrize("tekst", ["I have chest pain", "I can't breathe", "my lips are swollen", "she fainted",
                                   "I took too many pills", "I want to kill myself", "my baby has a fever"])
def test_urgjencat_ne_anglisht_kane_tekst_fiks_anglisht(tekst):
    from chatbot import kontrollo_urgjencen
    mesazhi = kontrollo_urgjencen(tekst, "en")
    assert mesazhi and ("127" in mesazhi) and ("Call" in mesazhi or "call" in mesazhi)


def test_urgjenca_anglisht_kapet_edhe_pa_zbulim_gjuhe():
    from chatbot import kontrollo_urgjencen
    assert kontrollo_urgjencen("chest pain", "sq")  # mesazh shqip, por rreziku kapet njësoj


@pytest.mark.parametrize("sq, en, ok", [
    ("Merr 1 tabletë 500 mg çdo 6 orë, maksimumi 4 g.", "Take 1 tablet of 500 mg every 6 hours, maximum 4 g.", True),
    ("Merr 1 tabletë 500 mg çdo 6 orë.", "Take 1 tablet of 50 mg every 6 hours.", False),
    ("Temperaturë mbi 39,5°C", "Fever above 39.5°C", True),
    ("Telefono 127 ose 112", "Call 127 or 112", True),
    ("Telefono 127 ose 112", "Call 112", False),
])
def test_kontrolli_i_numrave_te_perkthimi(sq, en, ok):
    assert numrat_perputhen(sq, en) is ok


@pytest.mark.sherbime
@pytest.mark.parametrize("tekst, pritet", [
    ("I have a headache", "dhimbje_koke"), ("I have a sore throat", "dhimbje_fyti"), ("I have diarrhea", "diarre"),
    ("I have heartburn after eating", "urth"), ("my back hurts", "dhimbje_shpine"), ("I can't sleep", "pagjumesi"),
    ("I have a dry cough", "kolle_thate"), ("I have hay fever and keep sneezing", "alergji"),
])
def test_simptomat_ne_anglisht(tekst, pritet):
    from chatbot import kerko_simptomat
    from gjuha import standardizo
    gjetur, _ = kerko_simptomat(standardizo(tekst))
    assert pritet in [s["id"] for s in gjetur], (tekst, standardizo(tekst), [s["id"] for s in gjetur])


@pytest.mark.sherbime
def test_urgjenca_anglisht_pergjigjet_anglisht_menjehere():
    from chatbot import Profili, pergjigju
    p = pergjigju("I have severe chest pain", [], Profili(), mendo=True)
    assert p.urgjence and p.gjuha == "en" and "Call 127" in p.tekst and p.sekonda < 5


@pytest.mark.llm
def test_pergjigjja_ne_anglisht_ruan_dozat():
    from chatbot import Profili, pergjigju
    p = pergjigju("I have a headache", [], Profili(mosha=30))
    assert p.gjuha == "en" and p.simptomat and "Headache" in p.tekst
    assert "500 mg" in p.tekst  # emri/doza e paracetamolit ruhet
