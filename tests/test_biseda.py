"""Biseda vazhdon natyrshëm, pa pasur nevojë të riniset, dhe përgjigjet nuk përsëriten.
Kërkon Neo4j + Ollama (bge-m3). Testet me LLM janë të shënuara @llm."""
import pytest

from chatbot import Profili, pergjigju

pytestmark = pytest.mark.sherbime


def test_bisede_e_plote_pa_rinisje(bisede):
    b = bisede()
    assert b.thuaj("Përshëndetje").qellimi == "pershendetje"
    p = b.thuaj("më dhemb dhëmbi")
    assert p.simptomat[0]["id"] == "dhimbje_dhembi" and p.barnat
    p = b.thuaj("faleminderit")
    assert p.qellimi == "faleminderit" and "dhëmbi" in p.tekst.lower()   # mban mend temën
    p = b.thuaj("sa herë në ditë ta marr?")
    assert p.qellimi == "doza" and "Doza" in p.tekst
    p = b.thuaj("kam të vjella")                                          # temë e re, pa rinisje
    assert [s["id"] for s in p.simptomat] == ["nauze_te_vjella"]
    p = b.thuaj("më dhemb veshi")
    assert [s["id"] for s in p.simptomat] == ["dhimbje_veshi"]
    p = b.thuaj("çfarë tjetër mund të bëj?")
    assert p.qellimi == "keshilla" and "vesh" in p.tekst.lower()
    assert b.thuaj("mirupafshim").qellimi == "mirupafshim"


def test_tema_e_vjeter_nuk_ngjitet_te_mesazhet_e_reja(bisede):
    """Gabimi i vjetër: pas 'më dhemb dhëmbi' çdo mesazh merrte përgjigje për dhëmbin."""
    b = bisede()
    b.thuaj("më dhemb dhëmbi")
    for mesazh in ["s'më zë gjumi", "kam urth", "më kruhet lëkura"]:
        p = b.thuaj(mesazh)
        assert "dhimbje_dhembi" not in [s["id"] for s in p.simptomat], mesazh


def test_kam_edhe_shton_simptomen(bisede):
    b = bisede()
    b.thuaj("kam temperaturë")
    p = b.thuaj("kam edhe dhimbje fyti")
    assert {"temperature", "dhimbje_fyti"} <= {s["id"] for s in p.simptomat}


def test_pyetja_sqaruese_per_kollen(bisede):
    b = bisede()
    p = b.thuaj("kam kollë")
    assert p.qellimi == "sqarim" and set(p.pritje) == {"kolle_thate", "kolle_gelbaze"}
    p = b.thuaj("e thatë")
    assert [s["id"] for s in p.simptomat] == ["kolle_thate"]


def test_pyetja_sqaruese_me_gelbaze(bisede):
    b = bisede()
    b.thuaj("kollitem shumë")
    p = b.thuaj("me gëlbazë të verdhë")
    assert [s["id"] for s in p.simptomat] == ["kolle_gelbaze"]


def test_sqarimi_ruan_simptomen_e_meparshme_me_edhe(bisede):
    b = bisede()
    b.thuaj("më dhemb dhëmbi")
    assert b.thuaj("kam edhe kollë").qellimi == "sqarim"
    p = b.thuaj("me gëlbazë")
    assert {"dhimbje_dhembi", "kolle_gelbaze"} <= {s["id"] for s in p.simptomat}


def test_zgjedhje_me_numer(bisede):
    b = bisede()
    p = b.thuaj("më dhemb")
    assert p.qellimi == "sqarim" and len(p.pritje) >= 2
    p = b.thuaj("2")
    assert [s["id"] for s in p.simptomat] == [p_id for p_id in b.pergjigjet[0].pritje[1:2]]


def test_pyetje_sqaruese_e_injoruar_kalon_te_tema_e_re(bisede):
    b = bisede()
    b.thuaj("kam kollë")
    p = b.thuaj("jo, më mirë më thuaj për dhimbjen e kokës")
    assert "dhimbje_koke" in [s["id"] for s in p.simptomat]


def test_gjendja_e_re_rillogarit_barnat_e_bisedes(bisede):
    b = bisede()
    p = b.thuaj("më dhemb koka")
    assert "ibuprofen" in {x["id"] for x in p.barnat}
    p = b.thuaj("jam shtatzënë")
    assert p.qellimi == "profil"
    assert "ibuprofen" not in {x["id"] for x in p.barnat}
    assert "paracetamol" in {x["id"] for x in p.barnat}


def test_alternativat_jane_barna_te_tjera(bisede):
    b = bisede()
    p1 = b.thuaj("kam alergji nga poleni")
    p2 = b.thuaj("a ka ndonjë ilaç tjetër?")
    assert p2.qellimi == "alternativa"
    assert not ({x["id"] for x in p1.barnat} & {x["id"] for x in p2.barnat})


def test_kur_duhet_mjeku(bisede):
    b = bisede()
    b.thuaj("më dhemb veshi")
    p = b.thuaj("kur duhet të shkoj te mjeku?")
    assert p.qellimi == "mjeku" and "qelb" in p.tekst


def test_info_per_semundjen(bisede):
    b = bisede()
    p = b.thuaj("çfarë është gripi?")
    assert p.qellimi == "info" and "virus" in p.tekst.lower()


def test_pyetje_per_ilac_me_emer_dhe_doza_vijuese(bisede):
    b = bisede()
    p = b.thuaj("çfarë është ibuprofeni?")
    assert p.qellimi == "ilac" and "Doza" in p.tekst
    p = b.thuaj("para apo pas ushqimit?")
    assert p.qellimi == "doza" and "Ibuprofen" in p.tekst


def test_ankese_e_panjohur_thuhet_sinqerisht(bisede):
    b = bisede()
    b.thuaj("më dhemb dhëmbi")
    p = b.thuaj("kam dridhje në gishta")
    assert p.qellimi == "e_panjohur" and not p.barnat


def test_bisede_e_thjeshte_nuk_fshin_kontekstin(bisede):
    b = bisede()
    b.thuaj("kam urth")
    b.thuaj("ok")
    b.thuaj("faleminderit")
    p = b.thuaj("sa herë ta marr?")
    assert p.qellimi == "doza" and "Antacid" in p.tekst


def test_vizitori_pa_moshe_merr_kujtese(bisede):
    p = bisede(Profili()).thuaj("më dhemb koka")
    assert "moshën" in p.tekst


# ------------------------------------------------------------ larmia e përgjigjeve
@pytest.mark.parametrize("mesazh", ["më dhemb koka", "kam diarre", "nuk më zë gjumi"])
def test_pergjigjet_nuk_jane_gjithmone_te_njejta(mesazh):
    tekste = {pergjigju(mesazh, [], Profili(mosha=30)).tekst for _ in range(8)}
    assert len(tekste) >= 3, "përgjigjet duhet të ndryshojnë"


def test_dy_pergjigje_rresht_nuk_perseriten(bisede):
    b = bisede()
    tekste = [b.thuaj(m).tekst for m in ["faleminderit", "faleminderit", "faleminderit"]]
    assert tekste[0] != tekste[1] != tekste[2]


def test_perseritja_e_simptomes_jep_permbledhje(bisede):
    b = bisede()
    p1 = b.thuaj("më dhemb koka")
    p2 = b.thuaj("më dhemb koka")
    assert p1.tekst != p2.tekst
    assert {x["id"] for x in p1.barnat} == {x["id"] for x in p2.barnat}   # përmbajtja e njëjtë, formulim tjetër


def test_permbajtja_e_sigurt_nuk_ndryshon_me_formulimin():
    """Larmia prek vetëm formulimin: barnat dhe shenjat e alarmit janë gjithmonë të njëjtat."""
    pergjigjet = [pergjigju("kam temperaturë", [], Profili(mosha=30)) for _ in range(6)]
    assert len({tuple(b["id"] for b in p.barnat) for p in pergjigjet}) == 1
    assert all("Shko te mjeku nëse" in p.tekst for p in pergjigjet)


# ------------------------------------------------------------ LLM (të ngadalta)
@pytest.mark.llm
def test_pyetje_e_lire_vijuese_me_llm(bisede):
    b = bisede()
    b.thuaj("kam diarre")
    p = b.thuaj("a mund të pi kafe?")
    assert p.qellimi == "llm" and len(p.tekst) > 20
    from chatbot import RE_DOZE
    pa_emra = p.tekst
    for x in p.barnat:
        pa_emra = pa_emra.replace(x["emer"], "")
    assert not RE_DOZE.search(pa_emra), "modeli nuk duhet të shkruajë doza me numra"


def test_filtri_i_dozave_te_modelit():
    from chatbot import ZEVENDESIM_DOZE, pastro_dozat
    barnat = [{"emer": "Ibuprofen 200/400 mg"}]
    tekst = "Merr **Ibuprofen 200/400 mg**.\nMerr 2 tableta 3 herë në ditë.\nPi shumë ujë."
    rezultat = pastro_dozat(tekst, barnat)
    assert "Ibuprofen 200/400 mg" in rezultat and "2 tableta" not in rezultat
    assert ZEVENDESIM_DOZE in rezultat and "Pi shumë ujë." in rezultat
    assert pastro_dozat("Merr 500 mg.\nMerr 1000 mg.", []).count(ZEVENDESIM_DOZE) == 1
