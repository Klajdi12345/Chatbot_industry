"""Njohja e simptomave nga mesazhe reale (me dhe pa ë/ç, me gabime të vogla, me fjalë të ndryshme).
Kërkon Neo4j + Ollama (bge-m3)."""
import pytest

from chatbot import kerko_simptomat

pytestmark = pytest.mark.sherbime

RASTET = [
    # dhimbje koke
    ("më dhemb koka", "dhimbje_koke"), ("me dhemb koka shume", "dhimbje_koke"),
    ("kam migrenë prej mëngjesit", "dhimbje_koke"), ("më çahet koka", "dhimbje_koke"),
    ("dhimbje në ballë", "dhimbje_koke"), ("kokëdhimbje", "dhimbje_koke"),
    # dhëmbi
    ("më dhemb dhëmbi", "dhimbje_dhembi"), ("me dhemb dhembi", "dhimbje_dhembi"),
    ("më dhemb dhëmballa e pasme", "dhimbje_dhembi"), ("më janë ënjtur mishrat e dhëmbëve", "dhimbje_dhembi"),
    # temperaturë, grip
    ("kam temperaturë", "temperature"), ("kam 39 gradë temperaturë", "temperature"), ("kam ethe", "temperature"),
    ("jam ftohur", "grip_ftohje"), ("kam grip", "grip_ftohje"), ("jam me virozë", "grip_ftohje"),
    # fyti, kolla, hunda
    ("më dhemb fyti", "dhimbje_fyti"), ("më dhemb fyti kur gëlltis", "dhimbje_fyti"),
    ("kam kollë të thatë", "kolle_thate"), ("kollë e thatë që s'më lë të fle", "kolle_thate"),
    ("kollitem dhe nxjerr gëlbazë", "kolle_gelbaze"), ("kam kollë me gëlbazë", "kolle_gelbaze"),
    ("më ka zënë hunda", "bllokim_hunde"), ("kam rrufë", "bllokim_hunde"), ("më rrjedhin hundët", "bllokim_hunde"),
    ("kam sinusit", "bllokim_hunde"),
    # alergji, lëkurë
    ("teshtij shumë dhe më lotojnë sytë", "alergji"), ("kam alergji nga poleni", "alergji"),
    ("më kruhet lëkura", "kruajtje_lekure"), ("më pickoi mushkonja", "kruajtje_lekure"),
    ("kam urtikarie", "kruajtje_lekure"), ("më kruhet mes gishtave të këmbës", "kerpudha_lekure"),
    ("kam kërpudha në lëkurë", "kerpudha_lekure"), ("kam lëkurë të thatë", "lekure_e_thate"),
    ("kam ekzemë në duar", "lekure_e_thate"), ("më plasaritet lëkura e duarve", "lekure_e_thate"),
    ("kam akne në fytyrë", "akne"), ("më dalin puçrra", "akne"), ("kam pika të zeza në hundë", "akne"),
    ("kam një lyth në gisht", "lytha_kallo"), ("kam kallo në këmbë", "lytha_kallo"),
    ("thoi i këmbës më është zverdhur", "kerpudha_thonjsh"), ("kam kërpudha në thonj", "kerpudha_thonjsh"),
    ("u dogja me ujë të nxehtë", "djegie_lekure"), ("më dogji dielli", "djegie_lekure"),
    ("u preva me thikë në gisht", "plage_e_vogel"), ("u gërvishta në gju", "plage_e_vogel"),
    # stomaku
    ("më djeg stomaku pas ngrënies", "urth"), ("kam urth", "urth"), ("kam refluks", "urth"),
    ("kam thartirë", "urth"), ("kam diarre", "diarre"), ("më ka prishur barku", "diarre"),
    ("kam jashtëqitje të lëngshme", "diarre"), ("kam kapsllëk", "kapsllek"),
    ("nuk kam dalë jashtë prej 3 ditësh", "kapsllek"), ("më fryhet barku", "fryrje_gazra"),
    ("kam shumë gazra", "fryrje_gazra"), ("kam ngërçe barku", "dhimbje_barku"),
    ("më dhemb barku", "dhimbje_barku"), ("kam të vjella", "nauze_te_vjella"),
    ("më përzihet", "nauze_te_vjella"), ("vjella gjithë natën", "nauze_te_vjella"),
    ("më përzihet në makinë", "semundje_udhetimi"), ("më bëhet keq në anije", "semundje_udhetimi"),
    ("kam hemorroide", "hemorroide"), ("kam majasëll", "hemorroide"),
    ("fëmija ka krimba", "krimba"), ("kam oksiure", "krimba"),
    # dhimbje trupi
    ("kam dhimbje menstruale", "dhimbje_menstruale"), ("më dhemb barku nga cikli", "dhimbje_menstruale"),
    ("më dhemb gjuri", "dhimbje_muskulore"), ("u ndrydha në këmbë", "dhimbje_muskulore"),
    ("më dhembin muskujt", "dhimbje_muskulore"), ("më dhemb qafa", "dhimbje_muskulore"),
    ("më dhemb shpina", "dhimbje_shpine"), ("më dhemb mesi", "dhimbje_shpine"), ("kam lumbago", "dhimbje_shpine"),
    # veshi, sytë, goja
    ("më dhemb veshi", "dhimbje_veshi"), ("më therr veshi", "dhimbje_veshi"), ("kam vesh të bllokuar", "dhimbje_veshi"),
    ("më thahen sytë", "sy_te_thate"), ("sy të lodhur nga kompjuteri", "sy_te_thate"),
    ("më janë skuqur sytë", "konjuktivit_alergjik"), ("kam konjuktivit", "konjuktivit_alergjik"),
    ("kam afte në gojë", "afte_gojore"), ("plagë në gjuhë", "afte_gojore"),
    ("kam herpes në buzë", "herpes_labial"), ("flluska në buzë", "herpes_labial"),
    ("më vjen erë goja", "ere_goje"), ("kam frymë të keqe", "ere_goje"),
    ("më është ngjirur zëri", "humbje_zeri"), ("kam humbur zërin", "humbje_zeri"),
    ("më rrjedh gjak nga hunda", "gjakderdhje_hunde"),
    # gjumi, stresi, të tjera
    ("nuk më zë gjumi", "pagjumesi"), ("s'më zë gjumi", "pagjumesi"), ("nuk fle dot natën", "pagjumesi"),
    ("kam pagjumësi", "pagjumesi"), ("kam ankth", "ankth_stres"), ("jam shumë i stresuar", "ankth_stres"),
    ("ndihem shumë i lodhur", "lodhje"), ("jam pa energji", "lodhje"),
    ("më merren mendtë", "marramendje"), ("kam marramendje", "marramendje"),
    ("më djeg kur urinoj", "cistit"), ("urinoj shumë shpesh dhe më djeg", "cistit"),
    ("kam kandidozë vaginale", "kandidoze_vaginale"), ("kam morra", "morra"), ("vajza ka morra", "morra"),
    ("kam zbokth", "zbokth"), ("luspa në flokë", "zbokth"),
    ("dua të lë duhanin", "lenie_duhani"), ("si ta lë cigaren", "lenie_duhani"),
    ("jam dehidratuar", "dehidratim_vape"), ("më bëri keq vapa", "dehidratim_vape"),
    # gegërisht, pa ë/ç, fjalë të përditshme (zgjerimi 2)
    ("më dhemb kryet", "dhimbje_koke"), ("kam zjarrmi", "temperature"), ("më dhemb gurmazi", "dhimbje_fyti"),
    ("më dhemb kurrizi", "dhimbje_shpine"), ("më shkon barku", "diarre"), ("kam barkqitje", "diarre"),
    ("kam bark të zënë", "kapsllek"), ("më ha lëkura", "kruajtje_lekure"), ("kam gastrit", "urth"),
    ("s'po më merr gjumi", "pagjumesi"), ("jam i këputur", "lodhje"), ("më merret mendja", "marramendje"),
    ("kam covid", "grip_ftohje"), ("kam angjinë", "dhimbje_fyti"), ("më dhemb supi", "dhimbje_muskulore"),
    ("kollë me flegmë", "kolle_gelbaze"), ("me dhemb barku nga regjimi", "dhimbje_menstruale"),
    # sëmundje dhe nevoja të reja
    ("çfarë vitamina të marr për dimër", "mungese_vitaminash"), ("dua të forcoj imunitetin", "mungese_vitaminash"),
    ("kam mungesë hekuri", "anemi_hekur"), ("më ka dalë hemoglobina e ulët", "anemi_hekur"),
    ("më mblidhen këmbët natën", "ngerce_kembesh"), ("kam ngërç në pulpë", "ngerce_kembesh"),
    ("po i dalin dhëmbët foshnjës", "dalje_dhembesh"), ("beba ka skuqje nga pelena", "skuqje_pelenash"),
    ("kam zgjebe", "zgjebe"), ("kam dyll në vesh", "dylle_veshi"),
    ("më ënjten këmbët në mbrëmje", "venat_kembe"), ("kam variçe", "venat_kembe"),
    ("si të mbrohem nga mushkonjat", "mbrojtje_insekte"), ("më ka kapur një rriqër", "mbrojtje_insekte"),
    ("kam lemzë", "lemza"), ("djersitem shumë", "djersitje"), ("më bien flokët", "renie_flokesh"),
    ("kam flluskë në thembër nga këpucët", "flluska_kembe"), ("më janë çarë buzët", "buze_te_thata"),
    ("më ngjiten sytë në mëngjes", "konjuktivit_infektiv"), ("dua të mbetem shtatzënë", "planifikim_shtatzenie"),
]


@pytest.mark.parametrize("tekst,priten", RASTET, ids=[r[0] for r in RASTET])
def test_simptoma_njihet(tekst, priten):
    gjetur, kandidatet = kerko_simptomat(tekst)
    ids = [s["id"] for s in gjetur]
    assert priten in ids, f"{tekst!r} → {ids} (kandidatë: {[s['id'] for s in kandidatet]})"


SIMPTOMA_TE_DYFISHTA = [
    ("kam temperaturë dhe më dhemb koka", {"temperature", "dhimbje_koke"}),
    ("më dhemb fyti dhe kam temperaturë", {"dhimbje_fyti", "temperature"}),
    ("kam diarre dhe të vjella", {"diarre", "nauze_te_vjella"}),
]


@pytest.mark.parametrize("tekst,priten", SIMPTOMA_TE_DYFISHTA)
def test_dy_simptoma_ne_nje_mesazh(tekst, priten):
    ids = {s["id"] for s in kerko_simptomat(tekst)[0]}
    assert priten <= ids, f"{tekst!r} → {ids}"


TE_PALIDHURA = ["kam humbur çelësat", "dua të blej makinë", "sa është ora?", "ku është farmacia më e afërt",
                "më pëlqen futbolli", "kam dridhje në gishta", "sot është ditë e bukur", "kam një pyetje"]


@pytest.mark.parametrize("tekst", TE_PALIDHURA)
def test_mesazhe_pa_lidhje_nuk_marrin_simptome(tekst):
    """Më mirë 'nuk e di' sesa një ilaç për diçka që personi nuk e ka."""
    assert kerko_simptomat(tekst)[0] == []
