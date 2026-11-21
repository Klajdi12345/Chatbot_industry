"""Ndërfaqja reale (Streamlit AppTest): regjistrimi me ç/ë nga formulari dhe biseda që vazhdon.
Kërkon Neo4j + Ollama."""
import uuid

import pytest
from streamlit.testing.v1 import AppTest

import llogarite
from conftest import ROOT

pytestmark = pytest.mark.sherbime
FJ = "Fjalekalim123"


def _app() -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def _regjistrohu(at: AppTest, perdoruesi: str, emer: str, fj: str = FJ, fj2: str | None = None, pelqim=True):
    form = [t for t in at.text_input]
    sipas_etiketes = {t.label: t for t in form}
    # Formulari i regjistrimit ka etiketat e veta; "Emri i përdoruesit" del te të dy formularët → i dyti.
    perdoruesit = [t for t in form if t.label == "Emri i përdoruesit"]
    perdoruesit[-1].input(perdoruesi)
    sipas_etiketes["Emri yt ose një pseudonim"].input(emer)
    sipas_etiketes["Fjalëkalimi (min. 8 karaktere)"].input(fj)
    sipas_etiketes["Përsërit fjalëkalimin"].input(fj2 if fj2 is not None else fj)
    if pelqim:
        at.checkbox[0].check()
    next(b for b in at.button if b.label == "Krijo llogarinë").click()
    at.run()
    return at


@pytest.fixture
def perdorues_testi():
    emrat = []

    def krijo(baza):
        u = f"{baza}_{uuid.uuid4().hex[:5]}"
        emrat.append(u)
        return u
    yield krijo
    for u in emrat:
        try:
            llogarite.fshi_llogari(u)
        except Exception:
            pass


def test_faqja_e_hyrjes_hapet():
    at = _app()
    assert any("Mirë se erdhe" in m.value for m in at.markdown)
    assert [b.label for b in at.button if "vizitor" in b.label]


@pytest.mark.parametrize("baza,emer", [("ëndrra_çela", "Ëndrra Çela"), ("john_smith", "John Smith"),
                                       ("ÇAJUPI", "Andon Çajupi")])
def test_regjistrimi_me_shkronja_shqipe_nga_formulari(perdorues_testi, baza, emer):
    u = perdorues_testi(baza)
    at = _regjistrohu(_app(), u, emer)
    assert not at.error, [e.value for e in at.error]
    assert at.session_state.llogaria["perdoruesi"] == u.lower()
    assert llogarite.hyr(u, FJ)


@pytest.mark.parametrize("perdoruesi,emer,fj2,pritet", [
    ("иван", "Ivan", None, "shkronja shqipe ose angleze"),
    ("ok_user", "Arben123", None, "Emri: 1–50"),
    ("ok_user2", "Arben", "TjeterFjalekalim", "nuk përputhen"),
])
def test_regjistrimi_refuzon_te_dhena_te_gabuara(perdoruesi, emer, fj2, pritet):
    at = _regjistrohu(_app(), perdoruesi, emer, fj2=fj2)
    assert any(pritet in e.value for e in at.error), [e.value for e in at.error]
    assert "llogaria" not in at.session_state


def test_biseda_si_vizitor_vazhdon_pa_rinisje():
    at = _app()
    next(b for b in at.button if "vizitor" in b.label).click()
    at.run()
    for mesazh in ["përshëndetje", "më dhemb koka", "faleminderit", "sa herë ta marr?", "kam edhe temperaturë"]:
        at.chat_input[0].set_value(mesazh).run()
        assert not at.exception, at.exception
    mesazhet = at.session_state.mesazhet
    assert len(mesazhet) == 10
    asistenti = [m["content"] for m in mesazhet if m["role"] == "assistant"]
    assert "Doza" in asistenti[3]                                        # pyetja vijuese mori dozat
    assert set(at.session_state.simptomat) >= {"dhimbje_koke", "temperature"}  # "edhe" u shtua
