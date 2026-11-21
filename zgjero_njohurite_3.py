"""Zgjerimi 3 i bazës së njohurive: shqipja e folur.

Fraza të reja për çdo simptomë, ashtu si i shkruajnë njerëzit në chat: gegërisht (Kosovë, veri),
toskërisht e folur, pa ë/ç, me "q" për "ç", me shkurtime ("m", "s'", "t'"). Bashkë me fjalorin
data/fjalori_shqip.json (gjuha.py) e bëjnë botën të kuptojë mesazhet pa i keqkuptuar.

Skripti është idempotent dhe ruan kopjen e vjetër te data/njohurite.para_zgjerimit_3.json.
Pas tij:  python ngarko_grafin.py
"""
import json
import shutil

from config import ROOT, normalizo

SKEDARI = ROOT / "data" / "njohurite.json"
KOPJA = ROOT / "data" / "njohurite.para_zgjerimit_3.json"

FRAZA = {
    "dhimbje_koke": ["m dhem kryt", "po m dhemb koka fort", "kom dhimje koke", "m plas kryet", "m rreh koka si çekiç",
                     "kokdhimbje qe prej mengjesit", "m dhemb koka mbrapa", "me dhem koka kur ngrihem"],
    "dhimbje_dhembi": ["m dhem dhambi", "po m dhemb dhamballa", "m dhemb nji dham", "dhambi m vret", "me dhemb dhembi poshte",
                       "m dhem mishi i dhambit", "nuk ha dot nga dhambi"],
    "temperature": ["kom zjarrmi", "jom me zjarrmi", "m ka ra temperatura 39", "kam temp 38 e gjysem", "jom nxeht krejt",
                    "fmija ka zjarrmi", "temperatura nuk po bie"],
    "grip_ftohje": ["jom ftof", "m ka zan gripi", "jom smut me grip", "kom grip e m dhemb krejt trupi", "jom ftof keq",
                    "kam ftohje me rrufe e koll", "po m kap ni grip"],
    "dhimbje_fyti": ["m dhem gurmazi", "m dhemb gryka", "kom gurmaz te skuqun", "nuk gelltis dot nga fyti",
                     "m djeg gurmazi kur pi uj", "kam bajamet te enjtura"],
    "kolle_thate": ["kom koll t thate", "po kollitem pa nxjerr kurgja", "koll e that natën", "kolla s m le me fjet",
                    "kolle e thate qe m gervisht"],
    "kolle_gelbaze": ["kom koll me glbaz", "nxjerr glbaz kur kollitem", "kolle me gelbaz te verdhe", "m mblidhet glbaza ne gjoks",
                      "koll e lagesht"],
    "bllokim_hunde": ["m ka zan hunda", "kom rruf", "po m pikojn hundt", "hundt m jan zan krejt", "nuk marr frym nga hunda natën",
                      "m rrjedh hunda uj"],
    "alergji": ["kom alergji", "po teshtij pa pushim", "m lotojn syt e teshtij", "alergjia e pranveres", "jom alergjik nga pluhni",
                "m kruhet hunda e teshtij"],
    "kruajtje_lekure": ["m ha lkura", "m kruhet lekura krejt", "m ka pick mushkonja", "m kan dal pika te kuqe qe m hajn",
                        "m pickoi nji insekt e u ajt", "m ha trupi naten"],
    "kerpudha_lekure": ["kom kerpudha te kamba", "m kruhet mes gishtave t kambes", "lekura mes gishtave u bardh e m ha",
                        "kerpudha ne lekure qe kruhen"],
    "urth": ["m djeg lukthi", "m djeg stomaku pas bukes", "kom thartira", "m vjen acidi n gryk", "m djeg nen gjoks kur ha",
             "kam urth gjith naten"],
    "diarre": ["m shkon barku", "barku m shkon uj", "kom diare prej 2 ditsh", "po dal shpesh ne wc me bark t lir",
               "m ka prish barku", "fmija ka diare"],
    "kapsllek": ["kom bark te zan", "s po dal dot jasht", "nuk kam dal ne wc 4 dit", "jom kapsllek", "barku m osht zan"],
    "fryrje_gazra": ["m fryhet barku", "kom gaza shum", "barku m osht ba si top", "jom fry pas ngranjes"],
    "dhimbje_barku": ["m dhem barku", "m dhemb lukthi", "m perdridhen zorrt", "kom dhimje barku", "m ther barku"],
    "dhimbje_menstruale": ["m dhemb barku nga cikli", "jom me cikel e m dhemb", "dhimje me rregulla", "m dhem mesi nga perioda",
                           "dhimbje te forta me menstruacione"],
    "dhimbje_muskulore": ["m dhemb krahu", "m dhem gjuni", "m dhembin eshtnat", "u ndrydha te kamba", "m dhemb qafa nga gjumi",
                          "m dhembin muskujt pas palestres", "kom dhimje ne sup"],
    "dhimbje_shpine": ["m dhem kurrizi", "m dhemb shpina posht", "m ka kap mesi", "nuk ngrihem dot nga mesi",
                       "m dhem shpina nga puna"],
    "nauze_te_vjella": ["m vjen me vjell", "po vjell", "m perzihet", "jom tu vjell gjith diten", "kom te perziera",
                        "fmija po vjell"],
    "semundje_udhetimi": ["m ba keq ne makin", "m perzihet kur udhetoj", "fmija vjell ne makine", "m vjen me vjell ne autobus",
                          "m ba keq ne aeroplan"],
    "dhimbje_veshi": ["m dhem veshi", "m ther veshi", "m dhembin veshat", "veshi m osht zan e m dhemb", "fmija ka dhimje veshi"],
    "pagjumesi": ["s po m merr gjumi", "nuk po fle naten", "s muj me fjet", "zgjohem naten e s fle ma", "kom pagjumesi",
                  "nuk m ze gjumi hiq"],
    "afte_gojore": ["kom afte n goj", "m ka dal ni plage n goj", "m djeg ni plage n gjuh", "plage e bardh ne goje"],
    "herpes_labial": ["m ka dal herpesi", "kom flluske n buz", "m doli ftohje ne buze", "m djeg buza e po m del flluske"],
    "hemorroide": ["kom hemoroide", "m del gjak kur dal n wc", "m dhem prapanica", "kom majasell"],
    "sy_te_thate": ["m thahen syt", "syt m djegin nga kompjuteri", "kom syt e lodhun", "m duket sikur kam rer n sy"],
    "konjuktivit_alergjik": ["m jan skuq syt e m kruhen", "syt t kuq nga alergjia", "m kruhen syt shum"],
    "akne": ["m dalin puqrra", "kom puqrra n fytyre", "kom akne", "m kan dal bibilaqe", "puqrra ne balle e mjeker"],
    "djegie_lekure": ["u dogja me uj t nxeht", "m dogj dielli", "u dogja me vaj", "m doli flluske nga djegia"],
    "plage_e_vogel": ["u preva me thik", "u gervishta", "kom ni plage t vogel", "m doli gjak nga nji prerje"],
    "morra": ["goca ka morra", "cuni ka morra n koke", "fmija ka morra prej shkolle"],
    "zbokth": ["kom zbokth", "m bien luspa nga koka", "m kruhet koka e m bie zbokth"],
    "kandidoze_vaginale": ["kom kandidoze", "m kruhet poshte e kam rrjedhje t bardhe", "kerpudha vaginale"],
    "cistit": ["m djeg kur shurrej", "m djeg kur bej pipi", "po shkoj shpesh me shurr", "kom infeksion t urines"],
    "marramendje": ["m merren mendt", "m vjen mendja rrotull", "m sillet krejt dhoma", "kom marrmendje kur ngrihem"],
    "lodhje": ["jom i lodhun gjith kohen", "jom pa fuqi", "jom i kputun", "s kam energji hiq"],
    "krimba": ["fmija ka krimba", "cunit i kruhet prapanica naten", "kam pa krimba te bardhe"],
    "lenie_duhani": ["du me lan duhanin", "si me e lan cigaren", "du me hjek cigaret"],
    "lekure_e_thate": ["m thahet lkura", "m jan qa duert", "lekura m plasaritet", "kom ekzeme"],
    "lytha_kallo": ["kom ni lyth", "kom kallo te kamba", "m ka dal ni lyth n gisht"],
    "kerpudha_thonjsh": ["thoi m osht verdh", "kom kerpudha n thoj", "thonjt e kambes m jan trash"],
    "gjakderdhje_hunde": ["m rrjedh gjak prej hunes", "m del gjak nga hunda", "fmijes i rrjedh gjak nga hunda"],
    "humbje_zeri": ["m ka ra zani", "s m del zani", "m osht ngjir zani"],
    "ere_goje": ["m vjen er goja", "goja m mban er t keqe"],
    "dehidratim_vape": ["m ka goditur dielli", "jom dehidratu", "kom etje t madhe nga vapa", "m ba keq nga nxehtesia"],
    "ankth_stres": ["jom nervoz", "kom ankth", "jom i stresum", "m rreh zemra nga merzia", "s qetesohem dot"],
    "mungese_vitaminash": ["du vitamina", "qfar vitamina me marr", "du me forcu imunitetin"],
    "anemi_hekur": ["kom hekur t ulet", "kom anemi", "m ka dal hemoglobina e ulet"],
    "ngerce_kembesh": ["m kap ngerqi n kambe naten", "m mblidhen kambet", "kom ngerqe ne pulpe"],
    "dalje_dhembesh": ["bebes po i dalin dhambet", "beba po nxjerr dhamb", "po i dalin dhambt"],
    "skuqje_pelenash": ["beba osht skuq nga pelena", "beba ka skuqje te pelena"],
    "zgjebe": ["kom zgjebe", "m ha naten mes gishtave", "krejt familja po kruhet"],
    "dylle_veshi": ["veshi m osht zan me dyll", "kom dyll n vesh", "s ndegjoj mir nga nji vesh"],
    "venat_kembe": ["m rendohen kambet", "kom variqe", "m ajten kambet ne mbramje"],
    "mbrojtje_insekte": ["si me u mbrojt prej mushkonjave", "m ka kap nji rriqer"],
    "lemza": ["m ka zan lemza", "s m ndalet lemza", "kom lemz"],
    "djersitje": ["djersitem shum", "m djersijn duert", "djerse e tepert nen sqetull"],
    "renie_flokesh": ["m bien flokt", "po m rrallohen flokt", "po m bien flok shum"],
    "flluska_kembe": ["m kan vra kepucet", "kom flluske n thember", "m doli flluske nga kepucet e reja"],
    "buze_te_thata": ["m jan qa buzt", "m thahen buzt", "buzt m plasariten"],
    "konjuktivit_infektiv": ["m ngjiten syt n mengjes", "kom qelb n sy", "syni m nxjerr qelb"],
    "planifikim_shtatzenie": ["du me met shtatzan", "po planifikojme nji fmij", "qfar me marr para shtatzanis"],
}


def main():
    data = json.loads(SKEDARI.read_text(encoding="utf-8"))
    if not KOPJA.exists():
        shutil.copy(SKEDARI, KOPJA)
    simptomat = {s["id"]: s for s in data["simptomat"]}
    te_reja = 0
    for sid, fraza in FRAZA.items():
        s = simptomat[sid]
        ekz = {normalizo(f) for f in s["fraza"]}
        for f in fraza:
            if normalizo(f) not in ekz:
                s["fraza"].append(f)
                ekz.add(normalizo(f))
                te_reja += 1
    SKEDARI.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gati: {te_reja} fraza të reja, gjithsej {sum(len(s['fraza']) for s in data['simptomat'])} fraza "
          f"për {len(data['simptomat'])} simptoma.")


if __name__ == "__main__":
    main()
