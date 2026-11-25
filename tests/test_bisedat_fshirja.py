"""Kur përdoruesi fshin një bisedë, ajo zhduket për të, por mbetet për administratorin."""
import pytest

from conftest import sherbimet_punojne

pytestmark = pytest.mark.sherbime
if not sherbimet_punojne():
    pytest.skip("Neo4j nuk po punon", allow_module_level=True)

import bisedat as db_b  # noqa: E402
import perdoruesit as db_p  # noqa: E402


@pytest.fixture
def personi():
    pid = db_p.shto_person("Prova fshirje")
    yield pid
    db_p.fshi_person(pid)


def test_biseda_e_fshire_zhduket_per_perdoruesin(personi):
    bid = db_b.krijo(personi, "Dhimbje koke")
    db_b.ruaj_mesazh(personi, bid, "user", "më dhemb koka")
    db_b.fshi(bid)
    assert bid not in [b["id"] for b in db_b.lista(personi)]
    assert not db_b.i_perket(personi, bid)          # nuk hapet, riemërtohet ose vazhdohet më


def test_admini_e_sheh_bisedan_e_fshire_me_mesazhet(personi):
    bid = db_b.krijo(personi, "Temperaturë")
    db_b.ruaj_mesazh(personi, bid, "user", "kam temperaturë")
    db_b.fshi(bid)
    b = next(x for x in db_b.lista_admin(personi) if x["id"] == bid)
    assert b["fshire"] is True and b["fshire_me"]
    assert [m["content"] for m in db_b.mesazhet(bid)] == ["kam temperaturë"]


def test_bisedat_e_pafshira_nuk_shenohen(personi):
    bid = db_b.krijo(personi, "Kollë")
    b = next(x for x in db_b.lista_admin(personi) if x["id"] == bid)
    assert b["fshire"] is False and b["fshire_me"] is None
    assert db_b.i_perket(personi, bid)


def test_fshirja_e_llogarise_i_fshin_edhe_bisedat_e_fshira():
    pid = db_p.shto_person("Prova llogari")
    bid = db_b.krijo(pid, "Biseda")
    db_b.fshi(bid)
    db_p.fshi_person(pid)
    assert db_b.mesazhet(bid) == [] and db_b.konteksti(bid) == {}
