"""Regjistrimi dhe hyrja: shkronjat shqipe (ç, ë) dhe angleze. Validimi nuk kërkon shërbime;
krijimi i llogarive kërkon Neo4j (llogaritë e testit fshihen në fund)."""
import uuid

import pytest

import llogarite

FJ = "Fjalekalim123"


@pytest.mark.parametrize("perdoruesi", [
    "arben", "John_Smith", "dritë", "çela", "Ëndrra", "ÇAJUP", "shqipëria.2025", "zhaklinë-ç", "anë_çezë",
    "abc", "a" * 30, "user.name-01",
])
def test_perdorues_i_vlefshem(perdoruesi):
    assert llogarite.valido(perdoruesi, FJ) is None


@pytest.mark.parametrize("perdoruesi", [
    "ab", "a" * 31, "emër me hapësirë", "иван", "用户", "user@mail", "emoji😀", "dritë!", "", "   ",
    "über", "señor", "łukasz",   # shkronja që nuk janë as shqipe as angleze
])
def test_perdorues_i_pavlefshem(perdoruesi):
    assert llogarite.valido(perdoruesi, FJ) is not None


def test_ë_e_dekompozuar_pranohet():
    """'ë' e shkruar si 'e' + diakritik (disa tastiera/telefona) normalizohet në 'ë'."""
    dekompozuar = "dri" + "t" + "ë"
    assert llogarite.valido(dekompozuar, FJ) is None
    assert llogarite.normalizo_perdoruesin(dekompozuar) == "dritë"


@pytest.mark.parametrize("fj,ok", [("1234567", False), ("12345678", True), (" fjalekalim", False),
                                   ("fjalëkalim", True), ("ççççëëëë", True)])
def test_fjalekalimi(fj, ok):
    assert (llogarite.valido("perdorues", fj) is None) == ok


@pytest.mark.parametrize("emer,ok", [
    ("Arbën Çela", True), ("Ëmëla", True), ("John O'Brien", True), ("Anë-Marie", True), ("", True),
    ("Arben123", False), ("<script>", False), ("Иван", False), ("a" * 51, False),
])
def test_emri(emer, ok):
    assert (llogarite.valido_emrin(emer) is None) == ok


# ------------------------------------------------------------------ me databazë
@pytest.fixture
def emer_testi():
    emrat = []

    def krijo(baza: str) -> str:
        u = f"{baza}_{uuid.uuid4().hex[:6]}"
        emrat.append(u)
        return u
    yield krijo
    for u in emrat:
        try:
            llogarite.fshi_llogari(u)
        except Exception:
            pass


@pytest.mark.sherbime
@pytest.mark.parametrize("baza,emer", [("tëst_çelë", "Arbëreshë Çela"), ("TEST_ËNDRRA", "Ëndrra"),
                                       ("test_english", "John Smith")])
def test_regjistrohu_dhe_hyr(emer_testi, baza, emer):
    from perdoruesit import merr_person
    u = emer_testi(baza)
    pid = llogarite.krijo_llogari(u, FJ, "perdorues", emer, 25)
    hyrja = llogarite.hyr(u, FJ)
    assert hyrja and hyrja["person_id"] == pid and hyrja["roli"] == "perdorues"
    assert hyrja["perdoruesi"] == u.lower()
    assert merr_person(pid)["emer"] == emer
    # Hyrja nuk dallon shkronjat e mëdha/të vogla dhe as hapësirat anash.
    assert llogarite.hyr(f"  {u.upper()} ", FJ)


@pytest.mark.sherbime
def test_fjalekalim_i_gabuar(emer_testi):
    u = emer_testi("test_gabim")
    llogarite.krijo_llogari(u, FJ)
    assert llogarite.hyr(u, "gabim12345") is None
    assert llogarite.hyr(u + "x", FJ) is None


@pytest.mark.sherbime
def test_perdorues_i_dyfishte(emer_testi):
    u = emer_testi("test_çift")
    llogarite.krijo_llogari(u, FJ)
    with pytest.raises(ValueError, match="ekziston"):
        llogarite.krijo_llogari(u.upper(), FJ)


@pytest.mark.sherbime
def test_regjistrim_i_pavlefshem_nuk_krijon_asgje():
    for u, fj, emer in [("иван_test", FJ, None), ("test_ok_" + uuid.uuid4().hex[:4], "123", None),
                        ("test_ok_" + uuid.uuid4().hex[:4], FJ, "<b>x</b>")]:
        with pytest.raises(ValueError):
            llogarite.krijo_llogari(u, fj, emer=emer)
        assert not llogarite.ekziston(u)


@pytest.mark.sherbime
def test_ndrysho_fjalekalimin_dhe_fshi(emer_testi):
    u = emer_testi("test_ndrysho_ë")
    llogarite.krijo_llogari(u, FJ)
    llogarite.ndrysho_fjalekalimin(u, "IRiÇëlës99")
    assert llogarite.hyr(u, FJ) is None
    assert llogarite.hyr(u, "IRiÇëlës99")
    llogarite.fshi_llogari(u)
    assert not llogarite.ekziston(u)
