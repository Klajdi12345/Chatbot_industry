"""Aplikacioni web (web/server.py): hyrja, regjistrimi, bisedat, profili, gjuha dhe paneli i adminit."""
import json
import os
import uuid

import pytest

from conftest import sherbimet_punojne

pytestmark = pytest.mark.sherbime
if not sherbimet_punojne():
    pytest.skip("Neo4j/Ollama nuk janë ndezur", allow_module_level=True)

from starlette.testclient import TestClient  # noqa: E402

import llogarite  # noqa: E402
from web.pergjigja import pa_emoji  # noqa: E402
from web.server import app  # noqa: E402

FJ = "Fjalekalim-123"


@pytest.fixture
def klienti():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def perdorues():
    emrat = []

    def krijo(baza="test_web"):
        u = f"{baza}_{uuid.uuid4().hex[:6]}"
        emrat.append(u)
        return u
    yield krijo
    for u in emrat:
        try:
            llogarite.fshi_llogari(u)
        except Exception:
            pass


def _biseda(c, mesazh, **kw):
    with c.stream("POST", "/api/biseda", json={"mesazh": mesazh, "mendo": False, **kw}) as r:
        assert r.status_code == 200, r.read()
        ngjarjet = [json.loads(x) for x in r.iter_lines() if x]
    assert ngjarjet[0]["lloji"] == "bisede"
    assert ngjarjet[-1]["lloji"] == "fund", ngjarjet[-1]
    return ngjarjet[0]["id"], ngjarjet[-1]["pergjigja"]


def test_faqja_dhe_ikonat(klienti):
    assert "FarmaBot" in klienti.get("/").text
    assert klienti.get("/static/app.js").status_code == 200
    assert klienti.get("/assets/ikona.png").status_code == 200


def test_pa_sesion_kerkon_hyrje(klienti):
    assert klienti.get("/api/sesioni").json()["llogaria"] is None
    assert klienti.get("/api/bisedat").status_code == 401


def test_vizitori_bisedon_dhe_profili_filtron_ilacet(klienti):
    klienti.post("/api/vizitor")
    r = klienti.put("/api/profili", json={"mosha": 30, "gjendjet": ["ulcer"], "shenime": ""})
    assert r.json()["profili"]["gjendjet"] == ["ulcer"]
    bid, p = _biseda(klienti, "më dhemb koka")
    emrat = [b["emer"].lower() for b in p["barnat"]]
    assert emrat and not any("ibuprofen" in e for e in emrat)            # ulçera e heq ibuprofenin
    assert any("ibuprofen" in x["emer"].lower() for x in p["te_perjashtuara"])
    # pyetja vijuese në të njëjtën bisedë mban mend ilaçet
    _, p2 = _biseda(klienti, "sa herë ta marr?", bisede_id=bid)
    assert "Doza" in p2["tekst"]
    lista = klienti.get("/api/bisedat").json()["bisedat"]
    assert [b["id"] for b in lista] == [bid]
    assert len(klienti.get(f"/api/bisedat/{bid}").json()["mesazhet"]) == 4


def test_urgjenca_pa_karta(klienti):
    klienti.post("/api/vizitor")
    _, p = _biseda(klienti, "kam dhimbje të fortë gjoksi dhe s'marr frymë")
    assert p["urgjence"] and not p["barnat"]


def test_teksti_pa_emoji(klienti):
    klienti.post("/api/vizitor")
    _, p = _biseda(klienti, "më dhemb koka")
    assert p["tekst"] == pa_emoji(p["tekst"])
    assert "**Simptom" in p["tekst"]                                       # bold-i nuk prishet


@pytest.mark.llm
def test_gjuha_e_nderfaqes_e_cakton_pergjigjen(klienti):
    klienti.post("/api/vizitor")
    _, p = _biseda(klienti, "më dhemb koka", gjuha="en")
    assert p["gjuha"] == "en"


def test_regjistrimi_bisedat_ruhen_dhe_fshihen(klienti, perdorues):
    u = perdorues()
    r = klienti.post("/api/regjistrohu", json={"perdoruesi": u, "fjalekalimi": FJ, "emer": "Test Web", "pelqim": True})
    assert r.status_code == 200 and r.json()["llogaria"]["perdoruesi"] == u
    bid, _ = _biseda(klienti, "kam temperaturë")
    assert klienti.patch(f"/api/bisedat/{bid}", json={"titull": "Temperatura"}).status_code == 200
    assert klienti.get("/api/bisedat").json()["bisedat"][0]["titull"] == "Temperatura"
    # pas daljes dhe hyrjes biseda është ende aty
    klienti.post("/api/dil")
    assert klienti.post("/api/hyr", json={"perdoruesi": u, "fjalekalimi": FJ}).status_code == 200
    mesazhet = klienti.get(f"/api/bisedat/{bid}").json()["mesazhet"]
    assert len(mesazhet) == 2 and mesazhet[1]["te_dhena"]["barnat"]       # kartat ruhen me mesazhin
    assert klienti.delete(f"/api/bisedat/{bid}").status_code == 200
    assert klienti.get("/api/bisedat").json()["bisedat"] == []


def test_regjistrimi_refuzon(klienti):
    r = klienti.post("/api/regjistrohu", json={"perdoruesi": "иван", "fjalekalimi": FJ, "pelqim": True})
    assert r.status_code == 400
    r = klienti.post("/api/regjistrohu", json={"perdoruesi": "ok_user_x", "fjalekalimi": FJ, "pelqim": False})
    assert r.status_code == 400 and "pëlqim" in r.json()["gabim"]
    assert klienti.post("/api/hyr", json={"perdoruesi": "nuk_ekziston", "fjalekalimi": "x"}).status_code == 401


def test_biseda_e_tjetrit_nuk_hapet(klienti, perdorues):
    klienti.post("/api/regjistrohu", json={"perdoruesi": perdorues(), "fjalekalimi": FJ, "pelqim": True})
    bid, _ = _biseda(klienti, "kam kollë")
    klienti.post("/api/regjistrohu", json={"perdoruesi": perdorues(), "fjalekalimi": FJ, "pelqim": True})
    assert klienti.get(f"/api/bisedat/{bid}").status_code == 404
    assert klienti.delete(f"/api/bisedat/{bid}").status_code == 404


def test_admini(klienti, perdorues):
    u = perdorues()
    klienti.post("/api/regjistrohu", json={"perdoruesi": u, "fjalekalimi": FJ, "pelqim": True})
    assert klienti.get("/api/admin/permbledhje").status_code == 403       # përdoruesi i thjeshtë jo
    llogarite.ndrysho_rolin(u, "admin")
    klienti.post("/api/hyr", json={"perdoruesi": u, "fjalekalimi": FJ})
    d = klienti.get("/api/admin/permbledhje").json()
    assert d["numrat"]["barna"] > 50
    assert any(x["perdoruesi"] == u for x in klienti.get("/api/admin/perdoruesit").json()["llogarite"])
    assert len(klienti.get("/api/admin/barnat").json()["barnat"]) == d["numrat"]["barna"]
    assert klienti.delete(f"/api/admin/perdoruesit/{u}").status_code == 400  # veten jo


def test_pa_emoji():
    assert pa_emoji("🩺 **Simptomat:** Dhimbje koke") == "**Simptomat:** Dhimbje koke"
    assert pa_emoji("**🩺 Simptomat:** a") == "**Simptomat:** a"
    assert pa_emoji("- 🧠 Po mendoj  ·  3 s") == "- Po mendoj · 3 s"
    assert pa_emoji("çaj → ëndërr") == "çaj → ëndërr"
