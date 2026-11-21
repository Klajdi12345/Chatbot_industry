"""Urgjencat kapen me rregulla, para çdo kërkimi ose modeli. Nuk kërkon shërbime."""
import pytest

from chatbot import MESAZH_VETEDEMTIM, kontrollo_urgjencen

URGJENCA = [
    "kam dhimbje gjoksi që shtrihet në krah",
    "më shtrëngon gjoksi",
    "nuk marr dot frymë",
    "kam vështirësi në frymëmarrje",
    "më zihet fryma",
    "më është ënjtur gjuha pas ilaçit",
    "më janë fryrë buzët dhe fyti",
    "babai ra pa ndjenja",
    "djali ka konvulsione",
    "fytyra e shtrembër dhe nuk lëviz dot krahun",
    "flas të ngatërruar papritur",
    "vjell gjak",
    "kollitem gjak",
    "kam jashtëqitje të zezë",
    "diarre me gjak",
    "fëmija gëlltiti ilaçe",
    "kam pirë shumë tableta",
    "mbidozë me paracetamol",
    "dhimbja e kokës më e fortë e jetës",
    "foshnja 2 muajshe ka temperaturë",
    "MË SHTRËNGON GJOKSI",            # shkronja të mëdha
    "me dhemb gjoksi",                 # pa ë
]
JO_URGJENCE = [
    "më dhemb koka", "kam temperaturë 38", "kam kollë të thatë", "më dhemb fyti kur gëlltit",
    "kam diarre", "teshtij shumë", "më dhemb dhëmbi", "kam urth pas ngrënies", "më dhemb shpina",
    "nuk më zë gjumi", "kam afte në gojë", "më është ngjirur zëri", "më rrjedh gjak nga hunda pak",
]
VETEDEMTIM = ["dua të vras veten", "nuk dua të jetoj më", "mendoj për vetëvrasje", "dua të dëmtoj veten"]


@pytest.mark.parametrize("tekst", URGJENCA)
def test_urgjenca_kapet(tekst):
    m = kontrollo_urgjencen(tekst)
    assert m and "127" in m and "112" in m


@pytest.mark.parametrize("tekst", JO_URGJENCE)
def test_jo_urgjence(tekst):
    assert kontrollo_urgjencen(tekst) is None


@pytest.mark.parametrize("tekst", VETEDEMTIM)
def test_vetedemtim_merr_mesazh_te_vecante(tekst):
    assert kontrollo_urgjencen(tekst) == MESAZH_VETEDEMTIM
