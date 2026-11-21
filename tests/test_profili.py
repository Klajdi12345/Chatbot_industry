"""Leximi i profilit nga teksti dhe gjendjet automatike sipas moshës. Nuk kërkon shërbime."""
import pytest

from chatbot import Profili, lexo_profilin_nga_teksti, qellimi_bisedes, qellimi_vijues


@pytest.mark.parametrize("tekst,gjendja", [
    ("jam shtatzënë", "shtatzeni"), ("jam me barrë në muajin e 5", "shtatzeni"),
    ("i jap gji foshnjës", "gjidhenie"), ("kam pasur ulçerë", "ulcer"),
    ("kam probleme me veshkat", "veshka"), ("kam hepatit", "melci"),
    ("kam tension të lartë", "hipertension"), ("jam astmatik", "astme"),
    ("kam diabet tip 2", "diabet"), ("marr varfarinë", "antikoagulante"),
    ("marr sertralinë", "antidepresive"), ("kam alergji nga ibuprofeni", "alergji_nsaid"),
    ("kam epilepsi", "epilepsi"), ("marr xanax për ankthin", "sedative"),
    ("kam problem me tiroiden", "tiroide"), ("jam në kimioterapi", "imunitet"),
])
def test_gjendja_lexohet(tekst, gjendja):
    gjendjet, _ = lexo_profilin_nga_teksti(tekst)
    assert gjendja in gjendjet


@pytest.mark.parametrize("tekst,gjendja", [
    ("nuk jam shtatzënë", "shtatzeni"), ("s'kam diabet", "diabet"), ("nuk kam astmë", "astme"),
])
def test_mohimi(tekst, gjendja):
    gjendjet, _ = lexo_profilin_nga_teksti(tekst)
    assert gjendja not in gjendjet


def test_afte_ne_goje_nuk_eshte_ulcere_stomaku():
    gjendjet, _ = lexo_profilin_nga_teksti("kam ulçerë në gojë")
    assert "ulcer" not in gjendjet


@pytest.mark.parametrize("tekst,mosha", [
    ("djali 5 vjeç ka temperaturë", 5), ("vajza 10 vjece", 10), ("bebja 8 muajshe", 0),
    ("kam 3 vite që kam diabet", None),
])
def test_mosha_lexohet(tekst, mosha):
    assert lexo_profilin_nga_teksti(tekst)[1] == mosha


@pytest.mark.parametrize("mosha,priten,nuk_priten", [
    (1, {"nen_2", "femije_nen_12", "nen_16"}, {"mbi_65"}),
    (8, {"femije_nen_12", "nen_16"}, {"nen_2"}),
    (14, {"nen_16"}, {"femije_nen_12"}),
    (30, set(), {"nen_2", "femije_nen_12", "nen_16", "mbi_65"}),
    (70, {"mbi_65"}, {"nen_16"}),
])
def test_gjendjet_automatike(mosha, priten, nuk_priten):
    g = Profili(mosha=mosha).te_gjitha_gjendjet()
    assert priten <= g and not (nuk_priten & g)


@pytest.mark.parametrize("tekst,qellimi", [
    ("Përshëndetje", "pershendetje"), ("tungjatjeta!", "pershendetje"), ("ckemi", "pershendetje"),
    ("mirëdita", "pershendetje"), ("faleminderit shumë", "faleminderit"), ("flm", "faleminderit"),
    ("rrofsh", "faleminderit"), ("mirupafshim", "mirupafshim"), ("natën e mirë", "mirupafshim"),
    ("si je?", "si_je"), ("kush je ti?", "kush_je"), ("çfarë di të bësh?", "kush_je"), ("ok", "pohim"),
])
def test_bisede_e_thjeshte(tekst, qellimi):
    assert qellimi_bisedes(tekst) == qellimi


@pytest.mark.parametrize("tekst", ["përshëndetje, më dhemb koka", "faleminderit, por kam edhe kollë",
                                   "mirëdita kam temperaturë"])
def test_pershendetje_me_ankese_nuk_eshte_bisede_e_thjeshte(tekst):
    assert qellimi_bisedes(tekst) is None


@pytest.mark.parametrize("tekst,qellimi", [
    ("sa herë në ditë ta marr?", "doza"), ("si merret?", "doza"), ("para apo pas ushqimit?", "doza"),
    ("a ka ndonjë ilaç tjetër?", "alternativa"), ("nuk më bëri efekt", "alternativa"),
    ("çfarë mund të bëj tjetër?", "keshilla"), ("ka ndonjë mjet natyral?", "keshilla"),
    ("kur duhet të shkoj te mjeku?", "mjeku"), ("a është e rrezikshme?", "mjeku"),
    ("çfarë është kjo?", "info"), ("pse ndodh?", "info"), ("a ngjitet?", "info"), ("sa zgjat zakonisht?", "info"),
])
def test_pyetje_vijuese(tekst, qellimi):
    assert qellimi_vijues(tekst) == qellimi
