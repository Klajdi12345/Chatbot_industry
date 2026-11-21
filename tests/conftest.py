"""Konfigurimi i testeve të FarmaBot-it.

Testet ndahen në:
  * pa shërbime  – të dhënat, urgjencat, profili, validimi i regjistrimit (punojnë gjithmonë);
  * @pytest.mark.sherbime – kanë nevojë për Neo4j + Ollama (bge-m3); anashkalohen nëse nuk janë ndezur;
  * @pytest.mark.llm      – thërrasin modelin gjuhësor (të ngadalta). Ekzekuto me:  pytest -m llm
"""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# Ndërfaqja në teste: pa "mendim të thellë" (modeli me thinking zgjat minuta). Testet e tij janë te -m llm.
os.environ.setdefault("FARMABOT_MENDO", "0")


def pytest_configure(config):
    config.addinivalue_line("markers", "sherbime: kërkon Neo4j dhe Ollama")
    config.addinivalue_line("markers", "llm: thërret modelin gjuhësor (i ngadaltë)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("-m"):
        return
    skip = pytest.mark.skip(reason="testet me LLM: ekzekutoji me  pytest -m llm")
    for item in items:
        if "llm" in item.keywords:
            item.add_marker(skip)


_sherbimet = None


def sherbimet_punojne() -> bool:
    global _sherbimet
    if _sherbimet is None:
        try:
            from config import embed, kontrollo_lidhjen
            kontrollo_lidhjen()
            embed(["prove"])
            _sherbimet = True
        except Exception:
            _sherbimet = False
    return _sherbimet


@pytest.fixture(autouse=True)
def _kontrollo_sherbimet(request):
    if request.node.get_closest_marker("sherbime") or request.node.get_closest_marker("llm"):
        if not sherbimet_punojne():
            pytest.skip("Neo4j ose Ollama nuk janë ndezur (nis FarmaBot-in)")
        import chatbot
        chatbot.vendos_farën(1234)


@pytest.fixture(scope="session")
def njohurite() -> dict:
    return json.loads((ROOT / "data" / "njohurite.json").read_text(encoding="utf-8"))


class Bisede:
    """Simulon një bisedë si faqja e chat-it: mban historinë dhe kontekstin ndërmjet mesazheve."""

    def __init__(self, profili=None):
        from chatbot import Konteksti, Profili
        self.profili = profili or Profili(mosha=30)
        self.historia: list[dict] = []
        self.konteksti = Konteksti()
        self.pergjigjet = []

    def thuaj(self, mesazh: str):
        from chatbot import Profili, pergjigju
        p = pergjigju(mesazh, self.historia, self.profili, konteksti=self.konteksti)
        if p.simptomat:
            self.konteksti.simptomat = [s["id"] for s in p.simptomat]
        if p.barnat_konteksti:
            self.konteksti.barnat = p.barnat_konteksti
        if not p.urgjence:
            self.konteksti.pritje, self.konteksti.pritje_shto = p.pritje, p.pritje_shto
        # Si paneli: gjendjet dhe mosha nga biseda mbeten për mesazhet e ardhshme.
        if p.gjendje_te_reja or p.mosha_e_re is not None:
            self.profili = Profili(mosha=p.mosha_e_re if p.mosha_e_re is not None else self.profili.mosha,
                                   gjendjet=self.profili.gjendjet | p.gjendje_te_reja, shenime=self.profili.shenime)
        self.historia += [{"role": "user", "content": mesazh}, {"role": "assistant", "content": p.tekst}]
        self.pergjigjet.append(p)
        return p


@pytest.fixture
def bisede():
    return Bisede
