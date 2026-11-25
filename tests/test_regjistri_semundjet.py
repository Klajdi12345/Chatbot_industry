"""Regjistri AKBPM dhe baza e sëmundjeve: kërkimi pa model gjuhësor dhe rregullat e sigurisë së përgjigjes.
Nuk kërkon Neo4j ose Ollama."""
import re

import pytest

import regjistri
import semundjet

RE_DOZE = re.compile(r"\b\d+\s*(mg|ml|tableta?|kapsula?)\s*(në ditë|çdo|x\s*\d)", re.I)


@pytest.mark.parametrize("teksti,celesi", [
    ("Çfarë është Augmentin?", ("augmentin",)),
    ("Xanax", ("ksanaks",)),
    ("Për çfarë përdoret Eliquis?", ("elikvis",)),
])
def test_emri_tregtar_gjendet(teksti, celesi):
    g = regjistri.gjej(teksti)
    assert g and g["lloji"] == "emer" and g["celesi"] == celesi


@pytest.mark.parametrize("teksti", ["amoksicilinë", "Amoxicillin", "amoksicilina"])
def test_lenda_aktive_pavaresisht_drejtshkrimit(teksti):
    g = regjistri.gjej(teksti)
    assert g and g["lloji"] == "lende" and g["emri"] == "AMOXICILLIN"


@pytest.mark.parametrize("teksti", ["më dhemb koka", "sot jam mirë", "kam temperaturë dhe kollë"])
def test_frazat_e_zakonshme_nuk_jane_ilac(teksti):
    assert regjistri.gjej(teksti) is None


@pytest.mark.parametrize("teksti", ["Xanax", "Augmentin", "Eliquis"])
def test_ilaci_me_recete_pa_doze_pa_sugjerim(teksti):
    g = regjistri.gjej(teksti)
    assert regjistri.eshte_pa_recete(g["produktet"]) is False
    t = regjistri.pergjigje(g, ka_simptoma=True)
    assert "Kërkon recetë" in t and "Nuk mund ta sugjeroj" in t
    assert not RE_DOZE.search(t)


def test_perjashtimet_nuk_gjenden():
    for fjala in list(regjistri.perjashtimet())[:50]:
        g = regjistri.gjej(fjala)
        assert g is None or g["celesi"] != (fjala,), fjala


def test_forma_shqip():
    assert regjistri.forma_shqip("film coated tablets") == "tableta të veshura me film"
    assert regjistri.forma_shqip("Prolonged-release hard capsules") == "kapsula me çlirim të zgjatur"


@pytest.mark.parametrize("teksti,id_", [
    ("Si trajtohet podagra?", "podagra"),
    ("What is gout?", "podagra"),
])
def test_semundja_gjendet(teksti, id_):
    assert [h["id"] for h in semundjet.gjej(teksti)] == [id_]


def test_emri_i_pergjithshem_jep_disa_hyrje():
    ids = {h["id"] for h in semundjet.gjej("Çfarë është diabeti?")}
    assert {"diabeti_tip1", "diabeti_tip2"} <= ids
    assert "disa sëmundje" in semundjet.pergjigje(semundjet.gjej("Çfarë është diabeti?"))


@pytest.mark.parametrize("teksti", ["më dhemb koka", "kam thyer krahun"])
def test_simptomat_nuk_jane_semundje(teksti):
    assert semundjet.gjej(teksti) == []


def test_pyetja_informuese():
    assert semundjet.eshte_pyetje_info("Si trajtohet podagra?")
    assert not semundjet.eshte_pyetje_info("më dhemb koka")


def test_pergjigja_e_semundjes_ka_burim_dhe_mjekun():
    t = semundjet.pergjigje(semundjet.gjej("Si trajtohet podagra?"), "Si trajtohet podagra?")
    assert "Burimi:" in t and "mjeku" in t


def test_cdo_hyrje_ka_fushat_kryesore():
    for h in semundjet.hyrjet():
        for f in ("id", "emri_shqip", "emri_anglisht", "pershkrimi", "simptomat", "burimi"):
            assert h.get(f), f"{h.get('id')}: mungon {f}"
        assert h["_rrenjet"], h["id"]
