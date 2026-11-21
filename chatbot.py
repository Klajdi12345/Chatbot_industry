"""Logjika e FarmaBot-it (GraphRAG): urgjenca → simptoma → ilaçe nga grafi → përgjigje.

Siguria nuk i lihet modelit gjuhësor:
  * urgjencat kapen me rregulla para se të pyetet modeli;
  * ilaçet e kundërindikuara për profilin hiqen me Cypher para se t'i shohë modeli;
  * dozat shfaqen nga databaza (kartat), jo nga teksti i modelit.

Biseda mban kontekstin (simptomat dhe ilaçet e fundit, pyetjen sqaruese në pritje), që personi
të vazhdojë natyrshëm: "faleminderit", "po sa herë ta marr?", "kam edhe kollë", "e thatë".
Përgjigjet ndërtohen nga disa formulime që nuk përsëriten njëra pas tjetrës.
"""
import json
import random
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache

from config import INDEKSI_PDF, chat, chat_mendo, embed, normalizo, query
from gjuha import anglisht_ne_shqip, gjuha_e_mesazhit, ka_shqip, ndryshimet, standardizo, varianta
from perkthimi import perkthe

PRAGU_SIMPTOMES = 0.68      # ngjashmëria minimale (cosine) që një simptomë të pranohet
DIFERENCA_MAKS = 0.05       # simptomat e tjera duhet të jenë afër më të mirës
BONUS_FJALE_KYCE = 0.12     # shtohet kur teksti përmend shprehimisht simptomën
MAKS_SIMPTOMA = 2
MAKS_SIMPTOMA_BASHKE = 3    # kur personi shton një simptomë ("kam edhe kollë")
MAKS_BARNA = 4
PRAGU_PDF = 0.60

_rng = random.Random()


def vendos_farën(fara: int | None):
    """Për teste: përgjigje të përsëritshme."""
    _rng.seed(fara)


# ---------------------------------------------------------------- urgjencat
# Teksti krahasohet pasi normalizohet (pa ë/ç, shkronja të vogla).
URGJENCAT = [
    (r"dhimbje (ne )?gjoks|me dhemb gjoksi|shtrengim (ne )?gjoks|me shtrengon gjoksi",
     "Dhimbja në gjoks mund të jetë shenjë e problemit me zemrën."),
    (r"nuk (marr|mund te marr|arrij te marr) (dot )?fryme|veshtiresi (ne|per) frymemarrje|"
     r"me zihet fryma|po mbytem|nuk kam ajer",
     "Vështirësia në frymëmarrje kërkon ndihmë të menjëhershme."),
    (r"(enjtur|enjtje|fryre)\w* (e |te )?(gjuh|buz|fyt)|(gjuh|buz|fyt)\w*( \w+){0,3} (enjt|fry)",
     "Ënjtja e gjuhës, buzëve ose fytit mund të jetë reaksion alergjik i rëndë (anafilaksi)."),
    (r"humb\w* ndjenja|ra pa ndjenja|pa ndjenja|te fiket|bie te fiket|konvulsion|kriz\w* epilept",
     "Humbja e ndjenjave ose konvulsionet kërkojnë ndihmë të menjëhershme."),
    (r"fytyra (e |me )?shtremb|nuk (levize|levizi|mund te levize) (dot )?(krahun|kemben|doren)|"
     r"paraliz|flas (te )?(ngaterruar|prapsht)|nuk flas dot",
     "Këto mund të jenë shenja të një goditjeje në tru (insult). Çdo minutë ka rëndësi."),
    (r"gjakderdhje (e madhe|qe nuk ndalet)|nuk (me )?ndalet gjaku|vjell\w* gjak|kollit\w* gjak|"
     r"jashteqitje( e| te)? (zeze|me gjak)|diarre me gjak|gjak ne jashteqitje",
     "Gjakderdhja kërkon kontroll mjekësor urgjent."),
    (r"mbidoz|kam pire shume (tableta|ilace|barna)|piu (shume )?(ilace|barna|tableta)|helmu|helmim|"
     r"gelltiti (ilace|barna|tableta)",
     "Mbidoza ose helmimi kërkon ndihmë të menjëhershme, edhe nëse personi ndihet mirë tani."),
    (r"dhimbj\w*( e)?( kok\w*)? (me e forte|me e madhe) (e|ne) jet",
     "Një dhimbje koke e papritur dhe shumë e fortë duhet parë menjëherë nga mjeku."),
    (r"(temperatur|ethe)\w*( \w+){0,4} (foshnj|bebe|i porsalindur)|(foshnj|bebe|porsalindur)\w*( \w+){0,4} (temperatur|ethe)",
     "Temperatura te një foshnjë e vogël (nën 3 muaj) duhet parë menjëherë nga mjeku."),
]
VETEDEMTIM = r"vetevras|te vras veten|vras veten|dua te vdes|te demtoj veten|nuk dua te jetoj"

MESAZH_URGJENCE = (
    "⚠️ **Kjo mund të jetë urgjencë.** {arsye}\n\n"
    "**Telefono menjëherë 127 (Urgjenca) ose 112**, ose shko në urgjencën më të afërt.\n\n"
    "Mos merr ilaçe pa folur më parë me personelin mjekësor."
)
MESAZH_VETEDEMTIM = (
    "Më vjen shumë keq që po kalon këtë. Nuk je vetëm dhe ka njerëz që mund të të ndihmojnë tani.\n\n"
    "**Nëse je në rrezik të menjëhershëm, telefono 127 ose 112.** Fol me dikë që i beson "
    "(familjar, mik) ose me mjekun tënd sa më shpejt. Nëse ke ilaçe pranë, largoji nga vetja."
)


# Të njëjtat urgjenca, me tekst fiks në anglisht (pa model: duhet të jetë i menjëhershëm dhe i saktë).
ARSYET_EN = [
    "Chest pain can be a sign of a heart problem.",
    "Difficulty breathing needs immediate help.",
    "Swelling of the tongue, lips or throat can be a severe allergic reaction (anaphylaxis).",
    "Loss of consciousness or seizures need immediate help.",
    "These can be signs of a stroke. Every minute matters.",
    "Bleeding like this needs urgent medical attention.",
    "An overdose or poisoning needs immediate help, even if the person feels fine now.",
    "A sudden, extremely severe headache must be seen by a doctor right away.",
    "A fever in a young baby (under 3 months) must be seen by a doctor right away.",
]
MESAZH_URGJENCE_EN = (
    "⚠️ **This may be an emergency.** {arsye}\n\n"
    "**Call 127 (Albanian emergency) or 112 now**, or go to the nearest emergency department.\n\n"
    "Do not take any medicine before speaking to medical staff."
)
MESAZH_VETEDEMTIM_EN = (
    "I'm really sorry you're going through this. You are not alone, and there are people who can help you right now.\n\n"
    "**If you are in immediate danger, call 127 or 112.** Talk to someone you trust (family, a friend) or to your "
    "doctor as soon as possible. If you have medicines nearby, put them away from yourself."
)


def kontrollo_urgjencen(tekst: str, gjuha: str = "sq") -> str | None:
    # Edhe gegërisht/chat ("s'po muj me marr frym") dhe anglisht ("I can't breathe"), sido që të zbulohet gjuha.
    vs = list(dict.fromkeys(varianta(tekst) + [anglisht_ne_shqip(tekst)]))
    en = gjuha == "en"
    if any(re.search(VETEDEMTIM, t) for t in vs):
        return MESAZH_VETEDEMTIM_EN if en else MESAZH_VETEDEMTIM
    for i, (pattern, arsye) in enumerate(URGJENCAT):
        if any(re.search(pattern, t) for t in vs):
            return MESAZH_URGJENCE_EN.format(arsye=ARSYET_EN[i]) if en else MESAZH_URGJENCE.format(arsye=arsye)
    return None


# ---------------------------------------------------------------- profili
@dataclass
class Profili:
    mosha: int | None = None
    gjendjet: set[str] = field(default_factory=set)
    shenime: str = ""  # alergji ose barna të tjera, tekst i lirë

    def te_gjitha_gjendjet(self) -> set[str]:
        g = set(self.gjendjet)
        if self.mosha is not None:
            if self.mosha < 2:
                g.add("nen_2")
            if self.mosha < 12:
                g.add("femije_nen_12")
            if self.mosha < 16:
                g.add("nen_16")
            if self.mosha >= 65:
                g.add("mbi_65")
        return g

    @property
    def femije(self) -> bool:
        return self.mosha is not None and self.mosha < 12


# Gjendje që njihen kur personi i shkruan në bisedë (tekst i normalizuar).
GJENDJE_NGA_TEKSTI = {
    "shtatzeni": r"shtatzen|me barre",
    "gjidhenie": r"gjidhen|i jap gji|ushqej (foshnjen |femijen )?me gji",
    "ulcer": r"ulcer(?!\w* (ne |te )?goj)",
    "veshka": r"veshk",
    "melci": r"melci|hepatit|ciroz",
    "zemra": r"\bzemr|insuficienc|kardiak",
    "hipertension": r"tension (te |e )?(larte|lart)|hipertension",
    "astme": r"astm",
    "diabet": r"diabet",
    "glaukome": r"glaukom",
    "prostate": r"prostat",
    "alkool": r"alkool",
    "antikoagulante": r"varfarin|sintrom|antikoagul|hollim\w* (e |te )?gjak|xarelto|eliquis|clopidogrel",
    "antidepresive": r"antidepres|sertralin|fluoksetin|paroksetin|escitalopram|citalopram|venlafaksin",
    "alergji_nsaid": r"alergj\w*( \w+){0,3} (ibuprofen|aspirin|nsaid|brufen|nurofen|diklofenak|voltaren)",
    "alergji_paracetamol": r"alergj\w*( \w+){0,3} (paracetamol|panadol|efferalgan)",
    "alergji_antihistaminike": r"alergj\w*( \w+){0,3} antihistamin",
    "epilepsi": r"epileps",
    "sedative": r"qetesues|benzodiazepin|xanax|diazepam|lexotan|alprazolam|bromazepam|lorazepam",
    "tiroide": r"tiroid|levotiroksin|eutirox",
    "imunitet": r"imunitet (te |i )?dobet|kimioterapi|kemioterapi|\bhiv\b|transplant",
}
# "nuk jam shtatzënë", "jo, nuk kam", "s'kam diabet", "s kam astme" (pa "s" brenda fjalëve si "shumë")
MOHIM = r"(\b(nuk|jo)( \w+){0,2}|(^|\s)s'? ?(kam|jam|ka|kemi|marr|vuaj)( \w+)?) ?$"
MOSHA_NGA_TEKSTI = r"\b(\d{1,3}) ?(vjec|vjet|vjece)\b"  # jo "vite": "3 vite që kam diabet"
MUAJ_NGA_TEKSTI = r"\b(\d{1,2}) ?(muaj|muajsh|muajshe)\b"


def lexo_profilin_nga_teksti(tekst: str) -> tuple[set[str], int | None]:
    """Gjen gjendje dhe moshë te mesazhi, p.sh. 'jam shtatzënë', 'djali 5 vjeç', 'marr varfarinë'."""
    t = standardizo(tekst)
    gjendjet = set()
    for gid, pattern in GJENDJE_NGA_TEKSTI.items():
        m = re.search(pattern, t)
        # Mohim i thjeshtë: "nuk jam shtatzënë", "s'kam diabet"
        if m and not re.search(MOHIM, t[:m.start()]):
            gjendjet.add(gid)
    mosha = None
    if m := re.search(MOSHA_NGA_TEKSTI, t):
        mosha = int(m.group(1))
    elif re.search(MUAJ_NGA_TEKSTI, t):
        mosha = 0
    return gjendjet, mosha


@dataclass
class Pergjigje:
    tekst: str
    urgjence: bool = False
    simptomat: list = field(default_factory=list)
    barnat: list = field(default_factory=list)
    te_perjashtuara: list = field(default_factory=list)
    burime: list = field(default_factory=list)
    pa_doza: bool = False
    gjendje_te_reja: set = field(default_factory=set)   # të gjetura në këtë mesazh
    mosha_e_re: int | None = None
    qellimi: str = ""                                    # si u kuptua mesazhi (për teste dhe statistika)
    pritje: list = field(default_factory=list)           # simptoma kandidate kur bota pyet "cila nga këto?"
    pritje_shto: bool = False                            # përgjigja e pyetjes shtohet te simptomat e vjetra
    barnat_konteksti: list = field(default_factory=list)  # barnat për pyetjet vijuese ("sa herë ta marr?")
    hapat: list = field(default_factory=list)            # hapat e mendimit, për t'ia treguar personit
    mendimi_modelit: str = ""                            # arsyetimi i modelit (thinking), nëse ka
    kuptimi: str = ""                                    # si e kuptoi modeli mesazhin, në shqip standard
    sekonda: float = 0.0
    gjuha: str = "sq"                                    # gjuha e personit: "sq" ose "en"
    fleteudhezuesit: list = field(default_factory=list)  # pjesët zyrtare openFDA (anglisht) për kartat
    ne_anglisht: bool = False                            # teksti është shkruar drejt në anglisht (s'ka nevojë për përkthim)


@dataclass
class Konteksti:
    """Çfarë mban mend biseda nga mesazhet e mëparshme."""
    simptomat: list[str] = field(default_factory=list)
    barnat: list[str] = field(default_factory=list)
    pritje: list[str] = field(default_factory=list)
    pritje_shto: bool = False


# ---------------------------------------------------------------- formulime të ndryshme
def _zgjidh(opsionet: list[str], historia: list[dict] | None = None) -> str:
    """Zgjedh një formulim, duke shmangur ato të përdorura në 2 përgjigjet e fundit."""
    fundit = " ".join(m["content"] for m in (historia or [])[-4:] if m.get("role") == "assistant")
    te_reja = [o for o in opsionet if not o or o.split("{")[0].strip()[:30] not in fundit]
    return _rng.choice(te_reja or opsionet)


TE_PERSHENDETJES = [
    "Përshëndetje! 👋 Jam FarmaBot. Më trego si ndihesh dhe të ndihmoj me ilaçe pa recetë.",
    "Tungjatjeta! Si mund të të ndihmoj sot? Më shkruaj çfarë simptome ke.",
    "Mirë se erdhe! Më thuaj çfarë të shqetëson (p.sh. dhimbje, kollë, alergji) dhe e shohim bashkë.",
    "Përshëndetje! Jam këtu për pyetje rreth simptomave të lehta dhe ilaçeve pa recetë. Çfarë po ndjen?",
]
SI_JE = [
    "Mirë, faleminderit që pyet! 😊 Po ti, si ndihesh? Ke ndonjë simptomë që të shqetëson?",
    "Jam gati të të ndihmoj! Si je ti? Më trego nëse ke ndonjë shqetësim shëndetësor.",
    "Shumë mirë, faleminderit! Më thuaj si mund të të ndihmoj sot.",
]
FALEMINDERIT = [
    "S'ka përse! Shpresoj të përmirësohesh shpejt. 🌿",
    "Me kënaqësi! Nëse ke pyetje të tjera, jam këtu.",
    "Të lutem! Kujdesu për veten dhe mos harro të pish mjaftueshëm ujë.",
    "Gjithmonë! Nëse simptomat nuk përmirësohen, fol me farmacistin ose mjekun.",
]
FALEMINDERIT_ME_KONTEKST = [
    "S'ka përse! Nëse do, mund të të them si merret ilaçi ose çfarë tjetër mund të bësh për {s}.",
    "Me kënaqësi! Shpresoj që {s} të kalojë shpejt. Më pyet nëse të duhet diçka tjetër.",
    "Të lutem! Mos harro: nëse {s} përkeqësohet ose zgjat, shko te mjeku.",
]
MIRUPAFSHIM = [
    "Mirupafshim! Të uroj shëndet të mirë. 🌿",
    "Kalofsh mirë! Nëse të duhet sërish, jam këtu.",
    "Shëndet! Mos harro: në urgjencë telefono 127 ose 112.",
]
KUSH_JE = [
    "Jam **FarmaBot**, asistent informues farmacie në shqip. Më shkruaj simptomat (p.sh. *\"më dhemb koka\"*) "
    "dhe të sugjeroj ilaçe pa recetë të sigurta për profilin tënd, si merren dhe kur duhet mjeku. "
    "Mund të më pyesësh edhe për një ilaç me emër (p.sh. *\"çfarë është ibuprofeni?\"*).",
    "Unë të ndihmoj me **simptoma të lehta** dhe **ilaçe pa recetë**: të them çfarë mund të marrësh, dozën, "
    "kujdeset për shtatzëni, fëmijë ose sëmundje kronike, dhe kur duhet të shkosh te mjeku. "
    "Nuk zëvendësoj farmacistin ose mjekun.",
]
POHIM = [
    "Në rregull! Nëse të duhet diçka tjetër, më shkruaj.",
    "Mirë. A ke ndonjë pyetje tjetër?",
    "Dakord! Jam këtu nëse të duhet diçka.",
]
POHIM_ME_KONTEKST = [
    "Në rregull! Për {s} mund të më pyesësh p.sh. *\"sa herë ta marr?\"*, *\"çfarë tjetër mund të bëj?\"* "
    "ose *\"kur duhet të shkoj te mjeku?\"*.",
    "Mirë! Nëse do të dish dozën, alternativat ose këshilla për {s}, më thuaj.",
]

HYRJE = [
    "Më vjen keq që nuk ndihesh mirë.",
    "E kuptoj, {s} është e bezdisshme.",
    "Shpresoj të kalojë shpejt.",
    "Faleminderit që më tregove.",
    "Le ta shohim bashkë.",
    "",
]
HYRJE_BARNA = [
    "Mund të ndihmojnë këto ilaçe pa recetë:",
    "Këto ilaçe pa recetë janë të përshtatshme për ty:",
    "Opsionet pa recetë që të përshtaten janë:",
    "Për këtë zakonisht përdoren:",
]
SHENIM_DOZA = [
    "Dozën, sa herë në ditë dhe për sa ditë e gjen te kartat më poshtë dhe te fletëudhëzuesi i paketimit.",
    "Si merret secili e ke te kartat më poshtë (doza, maksimumi, kohëzgjatja).",
    "Te kartat poshtë ke dozën dhe sa ditë mund ta marrësh pa mjek.",
]
MBYLLJE = [
    "_Para se ta marrësh, konfirmoje me farmacistin._",
    "_Farmacisti mund ta konfirmojë zgjedhjen dhe dozën, sidomos nëse merr ilaçe të tjera._",
    "_Pyet farmacistin para se ta marrësh: ai sheh edhe ilaçet e tjera që përdor._",
]
FTESE_VIJUESE = [
    "\nMund të më pyesësh: *\"sa herë ta marr?\"*, *\"çfarë tjetër mund të bëj?\"* ose *\"kur duhet mjeku?\"*.",
    "\nNëse do, të them më shumë për njërin prej tyre ose çfarë mund të bësh pa ilaç.",
    "", "",
]
NUK_E_NJOH = [
    "Më vjen keq, për këtë nuk kam ende informacion të besueshëm në bazën time. "
    "Farmacisti ose mjeku mund të të ndihmojnë më mirë.",
    "Këtë simptomë nuk e gjej dot në bazën time të njohurive, dhe nuk dua të të jap informacion të pasigurt. "
    "Të lutem pyet farmacistin ose mjekun.",
    "Nuk jam i sigurt që e kuptova saktë, dhe nuk kam të dhëna për këtë rast. Mund ta përshkruash ndryshe? "
    "Përndryshe, farmacisti është zgjedhja më e mirë.",
]
SQARIM = [
    "Që të të ndihmoj, më trego pak më shumë:\n\n"
    "- **Çfarë ndjen dhe ku?** (p.sh. dhimbje koke, dhëmbi, barku, fyti, kollë, temperaturë, alergji, diarre, urth)\n"
    "- **Prej sa kohësh** e ke?\n"
    "- Plotëso **moshën** dhe gjendjet e tua në panelin majtas (shtatzëni, ulçerë, ilaçe që merr...).",
    "Më përshkruaj pak simptomat: **çfarë** ndjen, **ku** dhe **prej sa kohësh**. "
    "P.sh. *\"më dhemb fyti prej 2 ditësh\"* ose *\"kam diarre që nga dje\"*.",
    "Nuk e kuptova plotësisht. Më shkruaj simptomën me fjalët e tua, p.sh. *\"më djeg stomaku pas ngrënies\"*, "
    "*\"teshtij shumë\"* ose *\"nuk më zë gjumi\"*.",
]
PYETJE_SQARUESE = SQARIM[0]  # përputhshmëri me kodin e vjetër


# ---------------------------------------------------------------- njohja e qëllimit
def _pastro(t: str) -> str:
    return re.sub(r"[^\w' ]+", " ", t).strip()


BISEDE = [  # (qëllimi, pattern) – vetëm për mesazhe të shkurtra pa ankesa
    ("mirupafshim", r"\b(mirupafshim|naten e mire|bye|shihemi|dite te mbare|ciao|kalofsh mire)\b"),
    ("faleminderit", r"\b(faleminderit|flm|rrofsh|thank\w*|merci|te lumte|ju lumte|shume mire|super|perfekt)\b"),
    ("kush_je", r"kush je|cfare je|cfare (di|mund) (te )?(besh|bej)|si funksionon|si (me|mund te me) ndihmon|^ndihme$"),
    ("si_je", r"\bsi (je|jeni|kalon|po ia kalon|ia kalon)\b"),
    ("pershendetje", r"^(pershendetje|tung\w*|ckemi|c'kemi|cfare ka|hello|hi|hey|alo|"
                     r"mire ?dita|mire ?mbrema|mire ?mengjes|mire se ju gjeta)\b"),
    ("pohim", r"^(ok|okej|okay|mire|ne rregull|dakord|kuptova|po|aha|ashtu|ne rregull faleminderit)$"),
]
ANKESE_SIMPTOME = (r"dhemb|dhimbj|\bkam\b(?! (nje )?pyetje)|ndjej|ndihem|vuaj|simptom|semund|"
                   r"me (kruhet|djeg|therr|fryhet|rrjedh|del|dalin|merren|perzihet)")
ANKESE = ANKESE_SIMPTOME + r"|ilac|barn|tablet"
PYETJE = r"\?|^(a|si|sa|kur|pse|cfare|ku|po|mund|duhet|eshte|c')\b|\b(a mund|a duhet|a eshte|a ka)\b"

VIJUESE = [  # pyetje vijuese që marrin përgjigje nga databaza, pa LLM
    ("doza", r"\bsa (here|tableta|mg|kokrra|cope|dite|ore|shpesh)|doz|si (ta|t'i|ti|i|e|te) (marr|pi|perdor)|"
             r"si merret|si perdoret|kur (ta|t'i|ti) marr|para (apo|ose) pas|me ushqim|bark bosh|maksimum|per sa kohe"),
    ("keshilla", r"keshill|cfare (tjeter )?(te|mund te) bej|si (ta|te) (largoj|qetesoj|kaloj|lehtesoj)|pa ilac|"
                 r"natyral|ne shtepi|\bcaj"),
    ("alternativa", r"tjeter (ilac|bar)|ilac tjeter|alternativ|dicka tjeter|(nuk|s') ?(me )?(ben|beri) (efekt|pune|mire)|"
                    r"nuk me ndihmoi|pa efekt|me te forte|ndonje tjeter|tjeter\??$"),
    ("mjeku", r"kur (te |duhet te |duhet )?(shkoj|vete|thirr)|\bmjek|doktor|rrezik|serioz|shqetesues"),
    ("info", r"cfare eshte|c'eshte|ceshte|pse (me )?(ndodh|vjen|dhemb)|nga (vjen|shkaktohet)|shkak|ngjitet|"
             r"sa (zgjat|kohe zgjat)|kalon vete"),
]
SHTESE = r"\b(edhe|gjithashtu|po ashtu|plus|bashke me|dhe nje)\b"

# Fjalë të përgjithshme që kanë disa simptoma: pyet në vend që të hamendësosh.
GRUPET = [
    (r"\bkoll", ["kolle_thate", "kolle_gelbaze"],
     "A është kolla **e thatë** (pa gëlbazë) apo **me gëlbazë**?"),
    (r"\bsy(te|ve|ri|rin)?\b", ["sy_te_thate", "konjuktivit_alergjik", "alergji"],
     "Si i ke sytë: **të thatë/të lodhur**, **të kuq që kruhen**, apo **lotojnë bashkë me teshtitje**?"),
]


def qellimi_bisedes(tekst: str) -> str | None:
    t = _pastro(standardizo(tekst))
    if not t or len(t.split()) > 6 or re.search(ANKESE, t):
        return None
    for q, pattern in BISEDE:
        if re.search(pattern, t):
            return q
    return None


def qellimi_vijues(tekst: str) -> str | None:
    t = standardizo(tekst)
    for q, pattern in VIJUESE:
        if re.search(pattern, t):
            return q
    return None


# ---------------------------------------------------------------- kërkimi në graf
_KOLONAT_SIMPTOMES = ("s.id AS id, s.emer AS emer, s.shenja_alarmi AS shenja_alarmi, s.keshilla AS keshilla, "
                      "s.fjale_kyce AS fjale_kyce, s.info AS info, s.kerkon_mjek AS kerkon_mjek")


# Fjalë që s'tregojnë simptomën (rrënjë 4 shkronja): "kam humbur çelësat" ≠ "kam humbur zërin".
_RRENJE_TE_PERGJITHSHME = {"dhem", "dhim", "ndih", "ndje", "humb", "shum", "edhe", "tani", "kohe", "dite",
                           "prej", "kete", "esht", "jane", "mund", "duhe", "bere", "kane", "gjit", "vazh",
                           "fort", "pak", "gjat", "here", "nate", "dick", "kemi", "jeni", "beje", "koll", "kruh",
                           "djeg", "skuq", "fryh", "therr", "keq", "tjet", "blej", "dua", "maki", "sot",
                           "ushq", "ngre", "pas", "para",
                           "shta"}  # "shtatzënë" është gjendje e profilit, jo simptomë
PRAGU_MBIVENDOSJES = 0.72  # fjalë e përbashkët pa fjalë kyçe pranohet vetëm me ngjashmëri të lartë


def _rrenjet(tekst: str) -> set[str]:
    return {f[:4] for f in re.findall(r"\w+", tekst) if len(f) >= 4} - _RRENJE_TE_PERGJITHSHME


def _rendit_simptomat(tekst: str, vetem: list[str] | None = None,
                      shtese: list[str] | None = None) -> list[dict]:
    """Kërkim me disa variante të mesazhit: origjinali, shqipja standarde (gjuha.py) dhe, në modalitetin
    e mendimit, formulimi i modelit. Për çdo simptomë mbahet varianti më i afërt."""
    vs = list(dict.fromkeys(varianta(tekst) + [normalizo(x) for x in (shtese or []) if x]))
    vektoret = embed(vs)
    rows_sipas_id = {}
    for v in vektoret:
        # Krahasohen të gjitha frazat (janë disa qindra); Neo4j e kthen ngjashmërinë si (1+cos)/2.
        for r in query(
            "MATCH (f:Fraze)-[:I_PERKET]->(s:Simptome) WHERE $vetem IS NULL OR s.id IN $vetem "
            "WITH s, f, vector.similarity.cosine(f.embedding, $v) AS sim ORDER BY sim DESC "
            "WITH s, collect(f.tekst)[0] AS fraza, max(sim) AS sim "
            f"RETURN {_KOLONAT_SIMPTOMES}, fraza, 2 * sim - 1 AS score",
            v=v, vetem=vetem,
        ):
            if r["id"] not in rows_sipas_id or r["score"] > rows_sipas_id[r["id"]]["score"]:
                rows_sipas_id[r["id"]] = r
    rows = list(rows_sipas_id.values())
    rrenjet = set().union(*(_rrenjet(x) for x in vs))
    for r in rows:
        r["fjale_kyce_gjetur"] = bool(r["fjale_kyce"] and any(re.search(r["fjale_kyce"], x) for x in vs))
        # Sinjal i vërtetë: fjalë kyçe, ose të paktën një fjalë kuptimplote e njëjtë me frazën më të afërt.
        r["i_sigurt"] = r["fjale_kyce_gjetur"] or (r["score"] >= PRAGU_MBIVENDOSJES and
                                                   bool(rrenjet & _rrenjet(r["fraza"] or "")))
        if r["fjale_kyce_gjetur"]:
            r["score"] += BONUS_FJALE_KYCE
    rows.sort(key=lambda r: -r["score"])
    return rows


PRAGU_KANDIDATEVE = 0.72  # pa sinjal të sigurt, por shumë afër → pyet "cila nga këto?"


def kerko_simptomat(tekst: str, shtese: list[str] | None = None) -> tuple[list[dict], list[dict]]:
    """Kërkim hibrid (vektorë bge-m3 + fjalë kyçe). Kthen (të zgjedhurat, kandidatet nëse është e paqartë)."""
    te_gjitha = _rendit_simptomat(tekst, shtese=shtese)
    rows = [r for r in te_gjitha if r["i_sigurt"]]
    if not rows or rows[0]["score"] < PRAGU_SIMPTOMES:
        # Vetëm ngjashmëri vektoriale pa asnjë fjalë të përbashkët: mos hamendëso.
        if re.search(ANKESE_SIMPTOME, standardizo(tekst)):
            return [], [r for r in te_gjitha if r["score"] >= PRAGU_KANDIDATEVE][:3]
        return [], []
    maks = rows[0]["score"]
    afer = [r for r in rows if r["score"] >= max(PRAGU_SIMPTOMES, maks - DIFERENCA_MAKS)]
    if len(afer) > MAKS_SIMPTOMA and not rows[0]["fjale_kyce_gjetur"]:
        return [], afer[:3]  # e paqartë (p.sh. vetëm "më dhemb") → pyet
    # Simptomat e përmendura shprehimisht (fjalë kyçe) pranohen edhe kur janë pak më larg.
    zgjedhura = [rows[0]] + [r for r in rows[1:] if r in afer or
                             (r["fjale_kyce_gjetur"] and r["score"] >= PRAGU_SIMPTOMES)]
    return zgjedhura[:MAKS_SIMPTOMA], []


def gjej_simptomat(tekst: str) -> list[dict]:
    return kerko_simptomat(tekst)[0]


def merr_simptomat_sipas_id(ids: list[str]) -> list[dict]:
    rows = query(f"MATCH (s:Simptome) WHERE s.id IN $ids RETURN {_KOLONAT_SIMPTOMES}, 1.0 AS score", ids=ids)
    return sorted(rows, key=lambda r: ids.index(r["id"]))


def merr_barnat(simptoma_ids: list[str], gjendjet: set[str], maks: int | None = MAKS_BARNA) -> tuple[list, list]:
    rows = query(
        "MATCH (s:Simptome)-[t:TRAJTOHET_ME]->(b:Barna) WHERE s.id IN $ids "
        "OPTIONAL MATCH (b)-[k:KUNDERINDIKOHET_PER]->(g:Gjendje) WHERE g.id IN $gj "
        "WITH s, t, b, collect(CASE WHEN g IS NULL THEN null "
        "  ELSE {gjendje: g.emer, arsye: k.arsye} END) AS kunder "
        "OPTIONAL MATCH (b)-[c:KUJDES_ME]->(g2:Gjendje) WHERE g2.id IN $gj "
        "RETURN s.id AS simptoma, t.rendi AS rendi, b {.*} AS barna, kunder, "
        "collect(CASE WHEN g2 IS NULL THEN null ELSE {gjendje: g2.emer, arsye: c.arsye} END) AS kujdes",
        ids=simptoma_ids, gj=sorted(gjendjet),
    )
    # Me disa simptoma barnat ndërthuren (1-ra e secilës, pastaj e 2-ta...), që secila të ketë ilaçin e vet.
    rows.sort(key=lambda r: (r["rendi"], simptoma_ids.index(r["simptoma"])))
    te_lejuara, te_perjashtuara, pare = [], [], set()
    for r in rows:
        b = r["barna"]
        if b["id"] in pare:
            continue
        pare.add(b["id"])
        if r["kunder"]:
            te_perjashtuara.append({"emer": b["emer"], "arsyet": r["kunder"]})
        else:
            te_lejuara.append({**b, "kujdes_profili": r["kujdes"]})
    return (te_lejuara[:maks] if maks else te_lejuara), te_perjashtuara


@lru_cache
def _ka_indeks_pdf() -> bool:
    return bool(query("SHOW VECTOR INDEXES YIELD name WHERE name = $n RETURN name", n=INDEKSI_PDF))


def kerko_ne_pdf(tekst: str, k: int = 3) -> list[dict]:
    try:
        if not _ka_indeks_pdf():
            return []
        v = embed([normalizo(tekst)])[0]
        rows = query(f"CALL db.index.vector.queryNodes('{INDEKSI_PDF}', $k, $v) YIELD node, score "
                     "RETURN node.tekst AS tekst, node.burimi AS burimi, node.faqja AS faqja, node.url AS url, "
                     "node.lloji AS lloji, 2 * score - 1 AS score",
                     k=k, v=v)
        return [r for r in rows if r["score"] >= PRAGU_PDF]
    except Exception:
        return []


# ---------------------------------------------------------------- LLM
SYSTEM_PROMPT = """Ti je FarmaBot, asistent informues farmacie që flet vetëm shqip të rregullt.
Ndihmon njerëzit të kuptojnë cilat ilaçe pa recetë mund të përdoren për simptoma të lehta.

RREGULLA TË DETYRUESHME:
1. Shkruaj vetëm në shqip, natyrshëm, shkurt dhe qartë (jo më shumë se 120 fjalë).
2. Përgjigju DREJTPËRDREJT pyetjes së fundit. Mos e përsërit përgjigjen e mëparshme.
3. Rekomando VETËM ilaçe nga lista "ILAÇE TË PËRSHTATSHME". Mos shpik ilaçe, emra apo fakte.
   Nëse lista është bosh, mos rekomando asnjë ilaç.
4. Mos shkruaj doza me numra. Thuaj që doza e saktë është te kartat dhe te fletëudhëzuesi i paketimit.
5. Nëse pyetja nuk ka lidhje me shëndetin ose ilaçet, thuaj me mirësjellje që ndihmon vetëm për këto.
6. Përmend shkurt kur duhet shkuar te mjeku, duke u bazuar te "SHENJA ALARMI".
7. Nëse ka ilaçe te "TË PËRJASHTUARA", shpjego me një fjali pse nuk janë të përshtatshme për këtë person.
8. Mos bëj diagnozë. Mbyll duke kujtuar që farmacisti ose mjeku duhet të konfirmojë."""


def _konteksti(profili: Profili, gjendjet_emra: list[str], simptomat, barnat, perjashtuara,
               pdf, pa_doza) -> str:
    rreshta = ["PROFILI I PERSONIT:"]
    rreshta.append(f"- Mosha: {profili.mosha if profili.mosha is not None else 'e panjohur'}")
    rreshta.append(f"- Gjendje: {', '.join(gjendjet_emra) or 'asnjë e deklaruar'}")
    if profili.shenime:
        rreshta.append(f"- Shënime (alergji/ilaçe të tjera): {profili.shenime}")
    if pa_doza:
        rreshta.append("- FËMIJË: mos jep doza; thuaj që doza varet nga pesha dhe ta pyesin farmacistin/pediatrin.")

    if simptomat:
        rreshta.append("\nSIMPTOMA TË IDENTIFIKUARA: " + ", ".join(s["emer"] for s in simptomat))
        for s in simptomat:
            if s.get("info"):
                rreshta.append(f"INFO ({s['emer']}): {s['info']}")
        rreshta.append("SHENJA ALARMI (kur duhet mjeku):")
        rreshta += [f"- {a}" for s in simptomat for a in s["shenja_alarmi"]]
        keshilla = [k for s in simptomat for k in (s.get("keshilla") or [])]
        if keshilla:
            rreshta.append("KËSHILLA TË PËRGJITHSHME:")
            rreshta += [f"- {k}" for k in keshilla]
    else:
        rreshta.append("\nSIMPTOMA TË IDENTIFIKUARA: asnjë. Pyet personin çfarë simptome ka.")

    rreshta.append("\nILAÇE TË PËRSHTATSHME:")
    if barnat:
        for b in barnat:
            rreshta.append(f"- {b['emer']} ({b['lende_aktive']}), p.sh. {', '.join(b['emra_tregtare'])}")
            for k in b["kujdes_profili"]:
                rreshta.append(f"    kujdes për këtë person: {k['arsye']}")
    else:
        rreshta.append("- (asnjë)")

    if perjashtuara:
        rreshta.append("\nTË PËRJASHTUARA PËR KËTË PERSON:")
        for p in perjashtuara:
            rreshta.append(f"- {p['emer']}: " + " ".join(a["arsye"] for a in p["arsyet"]))

    if pdf:
        rreshta.append("\nNGA FLETËUDHËZUESIT (PDF):")
        rreshta += [f"- [{d['burimi']}{', f.' + str(d['faqja']) if d.get('faqja') else ''}] {d['tekst'][:600]}"
                    for d in pdf]
    return "\n".join(rreshta)


def _lista(elemente: list[str]) -> str:
    if len(elemente) <= 1:
        return "".join(elemente)
    return ", ".join(elemente[:-1]) + " ose " + elemente[-1]


def _emrat(simptomat: list[dict]) -> str:
    emrat = [s["emer"].lower() for s in simptomat]
    return " dhe ".join(emrat) if len(emrat) <= 2 else ", ".join(emrat[:-1]) + " dhe " + emrat[-1]


def pergjigje_standarde(simptomat, barnat, perjashtuara, profili: Profili,
                        historia: list[dict] | None = None, perseritje: bool = False) -> str:
    emrat = " + ".join(s["emer"] for s in simptomat)
    s_tekst = _emrat(simptomat)
    p = []
    if perseritje:
        p.append(_zgjidh([f"Përsëri për {s_tekst}, ja përmbledhja:", f"Siç të thashë për {s_tekst}:",
                          f"Kthehemi te {s_tekst}:"], historia))
    else:
        hyrje = _zgjidh(HYRJE, historia).format(s=s_tekst)
        if hyrje:
            p.append(hyrje)
    p.append(f"🩺 **Simptoma:** {emrat}\n")
    if not perseritje:
        info = [s["info"] for s in simptomat if s.get("info")]
        if info:
            p.append("ℹ️ " + " ".join(info[:2]) + "\n")
    if any(s.get("kerkon_mjek") for s in simptomat):
        p.append("🩺 **Për këtë është mirë të flasësh me mjekun ose farmacistin**, sepse shkaku mund të kërkojë "
                 "kontroll ose ilaç me recetë.\n")
    if barnat:
        p.append(_zgjidh(HYRJE_BARNA, historia))
        for b in barnat:
            rresht = f"- **{b['emer']}** ({_lista(b['emra_tregtare'])})"
            if b["kujdes_profili"]:
                rresht += " — ⚠️ " + " ".join(k["arsye"] for k in b["kujdes_profili"])
            p.append(rresht)
        p.append("\n" + _zgjidh(SHENIM_DOZA, historia))
    elif perjashtuara:
        p.append("Nuk gjeta asnjë ilaç pa recetë që të jetë i sigurt për profilin tënd. "
                 "Të lutem fol me farmacistin ose mjekun.")
    else:
        p.append("Për këtë zakonisht nuk ka një ilaç pa recetë që ta zgjidhë; më shumë ndihmojnë këshillat më poshtë.")
    if perjashtuara:
        p.append("\n**Nuk t'i sugjeroj:** " + "; ".join(
            f"{x['emer']}: {' '.join(a['arsye'] for a in x['arsyet'])}" for x in perjashtuara))
    if profili.femije:
        p.append("\n👶 Për fëmijët doza varet nga pesha. Përdor formën pediatrike dhe pyet farmacistin ose pediatrin.")
    keshilla = [k for s in simptomat for k in (s.get("keshilla") or [])]
    if keshilla:
        p.append("\n**Këshilla:** " + " ".join(keshilla))
    alarmi = [a for s in simptomat for a in s["shenja_alarmi"]][:4]
    p.append("\n**Shko te mjeku nëse:**\n" + "\n".join(f"- {a}" for a in alarmi))
    if profili.mosha is None:
        p.append("\n_Nuk e di moshën tënde: plotësoje në panelin majtas që sugjerimet të jenë më të sakta._")
    p.append("\n" + _zgjidh(MBYLLJE, historia))
    if barnat and not perseritje:
        ftese = _zgjidh(FTESE_VIJUESE, historia)
        if ftese:
            p.append(ftese)
    return "\n".join(p)


# ---------------------------------------------------------------- pyetje për një ilaç
# Fjalë të id-ve që janë emra të përgjithshëm (jo emër ilaçi): "krem", "acid"...
_FJALE_TE_PERGJITHSHME = {"krem", "acid", "kripe", "pastile", "fyti", "xhel", "pika", "shampo", "losion",
                          "vaginal", "shpelares", "artificiale", "fiziologjike", "hemorroidesh", "emolient",
                          # fjalë që janë edhe pjesë e simptomës ("më dhemb veshi") ose emra të përgjithshëm
                          "veshi", "dylle", "balsam", "buzesh", "sprej", "supozitor", "vitamine", "vitamin",
                          "oksid", "zinku", "plaster", "hidrokoloid", "after", "repelent", "klorur", "alumini",
                          "paste", "leukoplast", "glycerin", "supposte", "hekur"}


@lru_cache
def _te_gjitha_barnat() -> list[dict]:
    rows = query("MATCH (b:Barna) OPTIONAL MATCH (s:Simptome)-[:TRAJTOHET_ME]->(b) "
                 "RETURN b {.*} AS b, collect(s.emer) AS per ORDER BY b.id")
    for r in rows:
        b = r["b"]
        fjale = set(b["id"].split("_")) | {normalizo(e).split(" ")[0] for e in b["emra_tregtare"]}
        fjale -= _FJALE_TE_PERGJITHSHME
        rrenjet = {f[:max(5, len(f) - 2)] for f in fjale if len(f) >= 4}
        r["pattern"] = r"\b(" + "|".join(sorted(map(re.escape, rrenjet))) + r")" if rrenjet else r"(?!)"
    return rows


def gjej_barnat_e_permendura(tekst: str) -> list[dict]:
    vs = varianta(tekst)
    return [r for r in _te_gjitha_barnat() if any(re.search(r["pattern"], t) for t in vs)]


def _barnat_sipas_id(ids: list[str]) -> list[dict]:
    sipas_id = {r["b"]["id"]: r for r in _te_gjitha_barnat()}
    return [sipas_id[i] for i in ids if i in sipas_id]


def pergjigje_per_ilacin(barnat: list[dict], profili: Profili, maks: int = 2) -> str:
    gjendjet = sorted(profili.te_gjitha_gjendjet())
    p = []
    for r in barnat[:maks]:
        b = r["b"]
        kunder = query("MATCH (b:Barna {id: $id})-[k:KUNDERINDIKOHET_PER]->(g:Gjendje) WHERE g.id IN $gj "
                       "RETURN g.emer AS gjendje, k.arsye AS arsye", id=b["id"], gj=gjendjet)
        kujdes = query("MATCH (b:Barna {id: $id})-[k:KUJDES_ME]->(g:Gjendje) WHERE g.id IN $gj "
                       "RETURN g.emer AS gjendje, k.arsye AS arsye", id=b["id"], gj=gjendjet)
        p.append(f"💊 **{b['emer']}** ({_lista(b['emra_tregtare'])})")
        if r["per"]:
            p.append(f"Përdoret për: {', '.join(r['per']).lower()}.")
        if kunder:
            p.append("\n⛔ **Nuk rekomandohet për ty:** " + " ".join(k["arsye"] for k in kunder)
                     + " Pyet farmacistin për një alternativë.\n")
            continue
        if profili.femije:
            p.append("\n👶 Për fëmijët doza varet nga pesha. Përdor formën pediatrike dhe pyet farmacistin.")
        else:
            p.append(f"\n- **Doza (të rritur):** {b['doza']}\n- **Maksimumi:** {b['doza_maks']}\n"
                     f"- **Kohëzgjatja:** {b['kohezgjatja']}\n- **Si merret:** {b['si_merret']}")
        for k in kujdes:
            p.append(f"- ⚠️ **{k['gjendje']}:** {k['arsye']}")
        for x in b.get("paralajmerime") or []:
            p.append(f"- {x}")
        p.append("")
    p.append("_Lexo fletëudhëzuesin e paketimit dhe konfirmoje me farmacistin._")
    return "\n".join(p)


def _shenim_profili(gjendje_te_reja: set[str], mosha_e_re: int | None) -> str:
    pjeset = []
    if mosha_e_re is not None:
        pjeset.append(f"mosha {mosha_e_re} vjeç" if mosha_e_re else "foshnjë nën 1 vjeç")
    if gjendje_te_reja:
        pjeset += [r["emer"].lower() for r in query(
            "MATCH (g:Gjendje) WHERE g.id IN $ids RETURN g.emer AS emer", ids=sorted(gjendje_te_reja))]
    return f"ℹ️ _E mora parasysh: {', '.join(pjeset)}._\n\n" if pjeset else ""


# ---------------------------------------------------------------- përgjigje vijuese nga databaza
def _vijuese_doza(kont: Konteksti, profili: Profili, historia) -> str | None:
    barnat = _barnat_sipas_id(kont.barnat)
    if not barnat:
        return None
    hyrje = _zgjidh(["Ja si merren ilaçet që të sugjerova:", "Sigurisht, ja dozat:",
                     "Ja udhëzimet për secilin:"], historia)
    return hyrje + "\n\n" + pergjigje_per_ilacin(barnat, profili, maks=3)


def _vijuese_alternativa(kont: Konteksti, profili: Profili, historia) -> tuple[str, list, list, list]:
    simptomat = merr_simptomat_sipas_id(kont.simptomat)
    te_gjitha, perjashtuara = merr_barnat(kont.simptomat, profili.te_gjitha_gjendjet(), maks=None)
    te_reja = [b for b in te_gjitha if b["id"] not in kont.barnat]
    s = _emrat(simptomat)
    if te_reja:
        p = [_zgjidh([f"Për {s} ka edhe këto opsione pa recetë:", f"Alternativa të tjera për {s}:",
                      f"Nëse ai nuk të ndihmoi, për {s} mund të provosh:"], historia)]
        p += [f"- **{b['emer']}** ({_lista(b['emra_tregtare'])})" +
              (" — ⚠️ " + " ".join(k["arsye"] for k in b["kujdes_profili"]) if b["kujdes_profili"] else "")
              for b in te_reja[:MAKS_BARNA]]
        p.append("\nMos i kombino pa pyetur farmacistin, sidomos ilaçet kundër dhimbjes.")
        barnat = te_reja[:MAKS_BARNA]
    else:
        p = [f"Për {s} nuk kam alternativa të tjera pa recetë që të përshtaten me profilin tënd."]
        barnat = []
    p.append("Nëse ilaçi nuk ka efekt pas disa ditësh, **shko te mjeku**: mund të duhet kontroll ose ilaç me recetë.")
    return "\n".join(p), barnat, perjashtuara, simptomat


def _vijuese_keshilla(simptomat: list[dict], historia) -> str:
    keshilla = [k for s in simptomat for k in (s.get("keshilla") or [])]
    s = _emrat(simptomat)
    if not keshilla:
        return f"Për {s} nuk kam këshilla të veçanta përveç pushimit dhe lëngjeve. Pyet farmacistin."
    hyrje = _zgjidh([f"Ja çfarë mund të bësh vetë për {s}:", f"Disa këshilla që ndihmojnë për {s}:",
                     f"Përveç ilaçeve, për {s} ndihmon:"], historia)
    return hyrje + "\n" + "\n".join(f"- {k}" for k in keshilla)


def _vijuese_mjeku(simptomat: list[dict], historia) -> str:
    s = _emrat(simptomat)
    hyrje = _zgjidh([f"Për {s}, shko te mjeku nëse:", f"Këto janë shenjat që për {s} duhet mjeku:",
                     f"Kujdes, për {s} duhet të shohë mjeku nëse:"], historia)
    alarmi = [a for x in simptomat for a in x["shenja_alarmi"]]
    return (hyrje + "\n" + "\n".join(f"- {a}" for a in alarmi) +
            "\n\nNë urgjencë (dhimbje gjoksi, vështirësi në frymëmarrje, të fikët) telefono **127** ose **112**.")


def _vijuese_info(simptomat: list[dict], historia) -> str:
    p = []
    for s in simptomat:
        p.append(f"**{s['emer']}:** {s.get('info') or 'Nuk kam përshkrim të detajuar për këtë.'}")
    p.append(_zgjidh(["\nNëse do, të them çfarë ilaçesh pa recetë ndihmojnë dhe kur duhet mjeku.",
                      "\nMund të më pyesësh edhe për ilaçet ose për këshilla që ndihmojnë.", ""], historia))
    return "\n".join(p).strip()


# ---------------------------------------------------------------- mendimi i thellë
class Mendimi:
    """Regjistron hapat e mendimit (shfaqen te ndërfaqja ndërsa ndodhin) dhe arsyetimin e modelit."""

    def __init__(self, aktiv: bool = False, on_hap=None, on_mendim=None, gjuha: str = "sq"):
        self.aktiv = aktiv
        self.gjuha = gjuha
        self.fillimi = time.perf_counter()
        self.hapat: list[str] = []
        self.mendimi = ""
        self.kuptimi = ""
        self.pyetje = ""
        self._on_hap, self._on_mendim = on_hap, on_mendim

    def hap(self, tekst: str, en: str | None = None):
        if self.gjuha == "en" and en:
            tekst = en
        if self.aktiv:
            tekst += f"  ·  {time.perf_counter() - self.fillimi:.0f} s"
        self.hapat.append(tekst)
        if self._on_hap:
            self._on_hap(tekst)

    def mendim(self, copa: str):
        self.mendimi += copa
        if self._on_mendim:
            self._on_mendim(copa)


PROMPT_KUPTIMI = """Ti je pjesa "kuptimi" e FarmaBot-it, një asistenti farmacie në shqip.
Njerëzit shkruajnë shqip të folur: gegërisht, pa ë/ç, me gabime shkrimi dhe shkurtime chat-i
(p.sh. "m dhem kryt" = më dhemb koka, "kom zjarrmi" = kam temperaturë, "s'po muj me fjet" = nuk mund të fle,
"m shkon barku" = kam diarre, "lukthi" = stomaku, "gurmazi" = fyti, "kurrizi" = shpina, "cuni" = djali,
"hiq" = fare, "hapa" = tableta).

Detyra:
1. Mendo shkurt dhe me kujdes çfarë thotë personi. Mos shto asgjë që nuk e tha.
2. "shqip_standard": mesazhi i rishkruar në shqip standard të rregullt.
3. "simptomat": simptomat që personi përmend vërtet, secila me 1–4 fjalë në shqip standard
   (p.sh. "dhimbje koke", "temperaturë", "diarre", "pagjumësi", "dhimbje stomaku pas ngrënies"). Bosh nëse s'ka.
4. "pyetje_sqaruese": nëse mesazhi është i paqartë, një pyetje e shkurtër në shqip; përndryshe "".

Kthe VETËM JSON: {"shqip_standard": "...", "simptomat": ["..."], "pyetje_sqaruese": ""}"""


@lru_cache
def _numri_frazave() -> int:
    return query("MATCH (f:Fraze) RETURN count(f) AS n")[0]["n"]


def _lexo_json(tekst: str) -> dict:
    m = re.search(r"\{.*\}", tekst or "", re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except ValueError:
        return {}


def kupto_me_modelin(mesazh: str, historia: list[dict], on_mendim=None) -> dict:
    """Modeli (me thinking) e kupton mesazhin dhe e rishkruan në shqip standard.
    Nuk zgjedh vetë nga baza: përputhjen me simptomat e bën gjithmonë kërkimi (vektorë + fjalë kyçe)."""
    mesazhet = [{"role": "system", "content": PROMPT_KUPTIMI}]
    fundit = [f"{'Personi' if x['role'] == 'user' else 'FarmaBot'}: {x['content'][:300]}" for x in historia[-2:]]
    mesazhet.append({"role": "user", "content":
                     ("Biseda më parë:\n" + "\n".join(fundit) + "\n\n" if fundit else "") +
                     f"Mesazhi i ri: {mesazh}\n(Fjalori automatik e lexon: {standardizo(mesazh)})"})
    pergjigja, _ = chat_mendo(mesazhet, on_mendim=on_mendim, format_json=True, num_predict=1000, temperatura=0.2)
    d = _lexo_json(pergjigja)
    simptomat = [x.strip() for x in (d.get("simptomat") or []) if isinstance(x, str) and x.strip()]
    return {"standard": str(d.get("shqip_standard") or "").strip(),
            "simptomat": list(dict.fromkeys(simptomat))[:4],
            "pyetje": str(d.get("pyetje_sqaruese") or "").strip()}


def _vlen_te_mendosh(t_norm: str, simptomat, kandidatet, kont: Konteksti, mesazh: str) -> bool:
    """Çdo mesazh shëndetësor rilexohet nga modeli. Përjashtim: pyetjet vijuese për temën e bisedës
    ("sa herë ta marr?") që marrin përgjigje të saktë nga databaza pa pasur nevojë për interpretim."""
    if simptomat or kandidatet or re.search(ANKESE_SIMPTOME, t_norm):
        return True
    return not ((kont.simptomat or kont.barnat) and qellimi_vijues(mesazh))


def _mendo_per_simptomat(mesazh: str, historia, simptomat, kandidatet, m: Mendimi):
    """Modeli kupton, baza vendos: formulimi i modelit shtohet si kërkim, por simptoma pranohet vetëm
    me të njëjtat rregulla (pragu i ngjashmërisë, fjalë kyçe ose fjalë e përbashkët)."""
    m.hap("🧠 Po mendoj më thellë: çfarë do të thotë saktësisht mesazhi?",
          "🧠 Thinking more deeply: what exactly does the message mean?")
    try:
        k = kupto_me_modelin(mesazh, historia, m.mendim)
    except Exception:
        m.hap("⚠️ Modeli gjuhësor nuk u përgjigj; vazhdoj vetëm me fjalorin dhe bazën.",
              "⚠️ The language model did not answer; continuing with the dictionary and the database.")
        return simptomat, kandidatet
    m.kuptimi, m.pyetje = k["standard"], k["pyetje"]
    if k["standard"]:
        m.hap(f"📝 E kuptova kështu: “{k['standard']}”", f"📝 I understood it as (in Albanian): “{k['standard']}”")
    if not k["simptomat"]:
        m.hap("Modeli nuk gjeti simptomë" + (f"; mbaj atë që gjeti baza: {_emrat(simptomat)}." if simptomat else "."),
              "The model found no symptom" + ("; keeping what the database found." if simptomat else "."))
        return simptomat, kandidatet
    m.hap("🤔 Simptomat që përmend: " + ", ".join(k["simptomat"]), "🤔 Symptoms mentioned: " + ", ".join(k["simptomat"]))
    m.hap("🔎 Po i krahasoj me bazën e njohurive...", "🔎 Comparing them with the knowledge base...")
    te_reja, kandidatet_e_reja = kerko_simptomat(mesazh, shtese=[k["standard"], *k["simptomat"]])
    if simptomat:
        # Rregullat dhe fjalët kyçe kanë gjetur diçka nga vetë fjalët e personit: ato kanë përparësi.
        # Modeli vetëm e konfirmon; nëse e lexon ndryshe, nuk e lejojmë të ndryshojë simptomat.
        if {x["id"] for x in te_reja} == {x["id"] for x in simptomat}:
            m.hap("✅ Modeli dhe baza përputhen: " + _emrat(simptomat),
                  "✅ The model and the database agree: " + _emrat(simptomat))
        else:
            m.hap(f"⚖️ Modeli e lexoi ndryshe; mbaj atë që gjeta nga fjalët e tua: {_emrat(simptomat)}.",
                  f"⚖️ The model read it differently; keeping what your own words say: {_emrat(simptomat)}.")
        return simptomat, kandidatet
    if te_reja:
        m.hap("✅ E konfirmova në bazë: " + _emrat(te_reja), "✅ Confirmed in the database: " + _emrat(te_reja))
        return te_reja, []
    if kandidatet_e_reja:
        m.hap("❔ Disa mundësi janë afër, por jo të sigurta: do të të pyes.",
              "❔ Several options are close but not certain: I will ask you.")
        return [], kandidatet_e_reja
    m.hap("❔ Në bazë nuk kam asgjë të sigurt për këtë: nuk hamendësoj.",
          "❔ Nothing certain in the database for this: I will not guess.")
    return [], kandidatet


# ---------------------------------------------------------------- rrjedha kryesore
def _zgjidh_pritjen(mesazh: str, pritje: list[str]) -> list[dict]:
    """Personi po i përgjigjet pyetjes 'cila nga këto?': gjen kandidatin që përmend."""
    t = standardizo(mesazh)
    kandidatet = merr_simptomat_sipas_id(pritje)
    if len(t.split()) <= 3 and (m := re.search(r"\b([1-3])\b|\be (para|dyta|treta)\b", t)):
        i = int(m.group(1)) - 1 if m.group(1) else {"para": 0, "dyta": 1, "treta": 2}[m.group(2)]
        return kandidatet[i:i + 1]
    te_pergjithshme = {"kolle", "dhimbje", "syte", "dhe", "ose", "nga", "kruhen"}
    for s in kandidatet:
        fjale = [f for f in re.findall(r"\w+", normalizo(s["emer"])) if f not in te_pergjithshme and len(f) >= 3]
        if any(re.search(r"\b" + re.escape(f[:max(4, len(f) - 2)]), t) for f in fjale):
            return [s]
    for s in kandidatet:
        if s["fjale_kyce"] and re.search(s["fjale_kyce"], t):
            return [s]
    rows = _rendit_simptomat(mesazh, vetem=pritje)
    if rows and rows[0]["score"] >= PRAGU_SIMPTOMES - 0.08:
        return [rows[0]]
    return []


def _pyetje_grupi(tekst: str, simptomat: list[dict]) -> tuple[list[str], str] | None:
    """Fjala e përgjithshme ("kollë") pa llojin ("e thatë") → pyetje. Një simptomë e grupit e gjetur vetëm
    nga ngjashmëria (pa fjalë kyçe) nuk mjafton: mund të jetë hamendësim."""
    t = standardizo(tekst)
    gjetur = {s["id"] for s in simptomat if s.get("fjale_kyce_gjetur", True)}
    for pattern, ids, pyetja in GRUPET:
        if re.search(pattern, t) and not gjetur & set(ids):
            return ids, pyetja
    return None


def _pyetje_kandidatesh(kandidatet: list[dict], historia) -> str:
    rreshta = "\n".join(f"{i}. {s['emer']}" for i, s in enumerate(kandidatet, 1))
    hyrje = _zgjidh(["Dua të sigurohem që të kuptova mirë. Cila nga këto të përshtatet më shumë?",
                     "Më ndihmo pak: me cilën nga këto ngjan më shumë?",
                     "Që të të jap informacionin e duhur, zgjidh njërën (mund të shkruash numrin):"], historia)
    return f"{hyrje}\n\n{rreshta}\n\nOse përshkruaje me fjalët e tua (ku dhemb, prej sa kohësh)."


def pergjigju(mesazh: str, historia: list[dict], profili: Profili,
              simptomat_e_meparshme: list[str] | None = None,
              konteksti: Konteksti | None = None, mendo: bool = False,
              on_hap=None, on_mendim=None) -> Pergjigje:
    """Përgjigjja e FarmaBot-it. Me mendo=True bota mendon më thellë (si Claude): modeli gjuhësor me
    thinking e rilexon mesazhin, baza e verifikon, dhe hapat shfaqen live (on_hap, on_mendim).
    Urgjencat dhe bisedat e thjeshta përgjigjen menjëherë, pa pritur modelin."""
    gjuha = gjuha_e_bisedes(mesazh, historia or [])
    m = Mendimi(aktiv=mendo, on_hap=on_hap, on_mendim=on_mendim, gjuha=gjuha)
    fillimi = time.perf_counter()
    p = _pergjigju(mesazh, historia, profili, simptomat_e_meparshme, konteksti, m)
    p.gjuha = gjuha
    gjetjet = []
    if m.aktiv and not p.urgjence and p.qellimi in ("simptome", "ilac", "profil", "alternativa", "doza"):
        gjetjet = _kerko_ne_burime(p, profili, m)
    if gjuha == "en" and not p.urgjence and not p.ne_anglisht:
        m.hap("🌐 Po e përkthej përgjigjen në anglisht...",
              "🌐 Translating the answer into English (glossary of medical terms; every number is checked)...")
        burimi = p.tekst
        for s_sq, s_en in _terma_per_perkthim(p).items():  # emrat e simptomave vendosen drejt në anglisht
            if s_sq in [x["emer"] for x in p.simptomat]:
                burimi = burimi.replace(s_sq, s_en).replace(s_sq.lower(), s_en.lower())
        p.tekst, ok = perkthe(burimi, terma=_terma_per_perkthim(p))
        if not ok:
            m.hap("⚠️ Përkthimi nuk u verifikua: po tregoj origjinalin shqip.",
                  "⚠️ The translation could not be verified: showing the original Albanian text.")
    if gjetjet:
        p.tekst += _tekst_i_gjetjeve(gjetjet, gjuha)
    p.hapat, p.mendimi_modelit, p.kuptimi = m.hapat, m.mendimi, m.kuptimi
    p.sekonda = time.perf_counter() - fillimi
    return p


def gjuha_e_bisedes(mesazh: str, historia: list[dict]) -> str:
    """Gjuha e mesazhit; për mesazhe neutrale ("ok", "2", "hello") vazhdon gjuhën e mesazhit të fundit."""
    if gjuha_e_mesazhit(mesazh) == "en":
        return "en"
    if not ka_shqip(mesazh):
        for x in reversed(historia):
            if x.get("role") == "user":
                return gjuha_e_mesazhit(x.get("content", ""))
    return "sq"


SEKSIONET_E_SIGURISE = ["do_not_use", "ask_doctor", "ask_doctor_or_pharmacist", "stop_use", "when_using",
                        "pregnancy_or_breast_feeding", "contraindications", "warnings_and_cautions", "drug_interactions",
                        "warnings", "use_in_specific_populations"]

# Gjendja e profilit → si shkruhet në fletëudhëzuesit e FDA-së (anglisht). Kontrolli bëhet me kod, jo me model.
GJENDJET_NE_FLETEUDHEZUES = {
    "shtatzeni": r"pregnan", "gjidhenie": r"breast[- ]?feed|nursing", "ulcer": r"ulcer|stomach bleeding",
    "veshka": r"kidney", "melci": r"liver", "zemra": r"heart (disease|failure|problem)|heart attack",
    "hipertension": r"high blood pressure|hypertension", "astme": r"asthma", "diabet": r"diabet",
    "glaukome": r"glaucoma", "prostate": r"prostate|trouble urinating", "alkool": r"alcohol|\bdrinks\b",
    "antikoagulante": r"anticoagula|blood thinn|warfarin", "antidepresive": r"MAOI|monoamine oxidase|antidepress",
    "epilepsi": r"seizure|epilep", "sedative": r"sedative|tranquili[sz]er|sleeping (aid|pill)",
    "tiroide": r"thyroid", "femije_nen_12": r"children under 12|under 12 years", "nen_2": r"under 2 years",
    "mbi_65": r"60 (years )?(of age )?(or|and) older|over 60|elderly",
}

_TERMA_EN = None


def _terma():
    global _TERMA_EN
    if _TERMA_EN is None:
        from config import ROOT
        _TERMA_EN = json.loads((ROOT / "data" / "terma_en.json").read_text(encoding="utf-8"))
    return _TERMA_EN


def _terma_per_perkthim(p: "Pergjigje") -> dict:
    """Fjalori i detyrueshëm për këtë përgjigje: emrat e simptomave të saj + termat e përgjithshëm."""
    t = _terma()
    terma = {s["emer"]: t["simptomat"][s["id"]] for s in p.simptomat if s["id"] in t["simptomat"]}
    return {**terma, **t["fjale"]}


def _burimet_e_ilaceve(ids: list[str]) -> list[dict]:
    return query("MATCH (c:Chunk {lloji: 'openfda'})-[:PERSHKRUAN]->(b:Barna) WHERE b.id IN $ids "
                 "AND c.seksioni IN $seksionet "
                 "RETURN b.id AS barna, b.emer AS emer, c.tekst AS tekst, c.burimi AS burimi, c.url AS url, "
                 "c.seksioni AS seksioni, c.lloji AS lloji, null AS faqja",
                 ids=ids, seksionet=SEKSIONET_E_SIGURISE)


def _kerko_ne_burime(p: "Pergjigje", profili: Profili, m: "Mendimi") -> list[dict]:
    """Kërkim i thellë në datasetet (pa model gjuhësor, që të mos shpikë ose të përkthejë gabim):
      * fletëudhëzuesit zyrtarë openFDA të ilaçeve të sugjeruara: a përmendin gjendjet e këtij personi?
      * MedlinePlus: tema për simptomat (lidhje për të lexuar më shumë).
    Nuk ndryshon ilaçet, dozat ose filtrimin; vetëm shton paralajmërime dhe burime."""
    # Edhe gjendjet/mosha që personi i shkroi në këtë mesazh ("jam shtatzënë", "djali 5 vjeç").
    profili = Profili(mosha=p.mosha_e_re if p.mosha_e_re is not None else profili.mosha,
                      gjendjet=profili.gjendjet | set(p.gjendje_te_reja), shenime=profili.shenime)
    ids = ([b["id"] for b in p.barnat] or p.barnat_konteksti)[:3]
    m.hap("📚 Po kërkoj në burimet zyrtare mjekësore (openFDA, MedlinePlus)...",
          "📚 Searching official medical sources (openFDA, MedlinePlus)...")
    try:
        pjeset = _burimet_e_ilaceve(ids) if ids else []
        temat = []
        for s in p.simptomat[:2]:
            emri_en = _terma()["simptomat"].get(s["id"], s["emer"])
            temat += [d for d in kerko_ne_pdf(emri_en, k=3) if d.get("lloji") == "medlineplus"][:1]
    except Exception:
        m.hap("⚠️ Burimet nuk janë të arritshme tani.", "⚠️ The sources are not reachable right now.")
        return []
    emrat = sorted({d["burimi"] for d in pjeset + temat})
    if not emrat:
        m.hap("Nuk gjeta asgjë shtesë në burime.", "Found nothing extra in the sources.")
        return []
    m.hap("📖 Po lexoj: " + ", ".join(emrat), "📖 Reading: " + ", ".join(emrat))
    gjendjet = profili.te_gjitha_gjendjet()
    gjetjet = []
    for bid in dict.fromkeys(d["barna"] for d in pjeset):
        tekstet = [d for d in pjeset if d["barna"] == bid]
        permend = [g for g in sorted(gjendjet) if g in GJENDJET_NE_FLETEUDHEZUES and any(
            re.search(GJENDJET_NE_FLETEUDHEZUES[g], d["tekst"], re.I) for d in tekstet)]
        if permend:
            gjetjet.append({"emer": tekstet[0]["emer"], "gjendjet": permend, "burimi": tekstet[0]["burimi"]})
    if gjetjet:
        eg = _emrat_e_gjendjeve()
        m.hap("⚠️ Fletëudhëzuesi zyrtar përmend gjendje të profilit tënd: " +
              "; ".join(f"{g['emer']} ({', '.join(eg.get(x, x).lower() for x in g['gjendjet'])})" for g in gjetjet),
              "⚠️ The official leaflet mentions conditions from your profile: " +
              "; ".join(f"{g['emer']} ({', '.join(g['gjendjet'])})" for g in gjetjet))
    elif gjendjet and pjeset:
        m.hap("✅ Fletëudhëzuesit zyrtarë nuk përmendin asnjë nga gjendjet e profilit tënd.",
              "✅ The official leaflets do not mention any of the conditions in your profile.")
    p.burime = (p.burime or []) + pjeset + temat
    p.fleteudhezuesit = pjeset
    return gjetjet


def _emrat_e_gjendjeve() -> dict:
    emrat = {r["id"]: r["emer"] for r in query("MATCH (g:Gjendje) RETURN g.id AS id, g.emer AS emer")}
    return emrat | {"femije_nen_12": "fëmijë nën 12 vjeç", "nen_2": "fëmijë nën 2 vjeç", "mbi_65": "mbi 65 vjeç"}


def _tekst_i_gjetjeve(gjetjet: list[dict], gjuha: str) -> str:
    emrat = _emrat_e_gjendjeve()
    if gjuha == "en":
        rreshta = [f"- **{g['emer']}**: the official leaflet mentions precautions for: "
                   + ", ".join(g["gjendjet"]).replace("_", " ") + f" [{g['burimi']}]" for g in gjetjet]
        return ("\n\n📄 **Official US leaflet (FDA) check:**\n" + "\n".join(rreshta) +
                "\n\nAsk the pharmacist before using it. The original text is in the card below.")
    rreshta = [f"- **{g['emer']}**: fletëudhëzuesi zyrtar përmend kujdes për: "
               + ", ".join(emrat.get(x, x).lower() for x in g["gjendjet"]) + f" [{g['burimi']}]" for g in gjetjet]
    return ("\n\n📄 **Kontroll në fletëudhëzuesin zyrtar (FDA, SHBA):**\n" + "\n".join(rreshta) +
            "\n\nPyet farmacistin para se ta përdorësh. Tekstin origjinal (anglisht) e ke te karta më poshtë.")


def _pergjigju(mesazh: str, historia: list[dict], profili: Profili,
               simptomat_e_meparshme: list[str] | None, konteksti: Konteksti | None,
               m: Mendimi) -> Pergjigje:
    """
    1. Urgjencë → mesazh fiks (127/112).
    2. Gjendje/moshë te mesazhi → shtohen te profili.
    3. Bisedë e thjeshtë (përshëndetje, faleminderit, mirupafshim) → përgjigje e shkurtër, konteksti mbetet.
    4. Përgjigje e pyetjes sqaruese ("e thatë", "2") → simptoma e zgjedhur.
    5. Pyetje për një ilaç me emër → përgjigje nga databaza.
    6. Simptomë e re → përgjigje nga databaza ("edhe" → shtohet te simptomat e mëparshme).
    7. Pyetje vijuese (doza, alternativa, këshilla, mjeku, info) → nga databaza; pyetje e lirë → LLM me kontekst.
    8. Ankesë që nuk e njoh → e them sinqerisht (nuk e lidh me temën e vjetër).
    """
    kont = konteksti or Konteksti(simptomat=list(simptomat_e_meparshme or []))
    historia = historia or []

    t_norm = standardizo(mesazh)
    urgjence = kontrollo_urgjencen(mesazh, m.gjuha)
    if urgjence:
        m.hap("🚨 Shenjë urgjence: përgjigjem menjëherë, pa pritur.", "🚨 Emergency sign: answering immediately, without waiting.")
        return Pergjigje(tekst=urgjence, urgjence=True, qellimi="urgjence")
    if nd := ndryshimet(mesazh):
        m.hap("📖 E lexova mesazhin: " + ", ".join(f"“{a}” → “{b}”" for a, b in nd[:6]),
              "📖 Read the message (Albanian reading: “" + t_norm + "”)")
    else:
        m.hap("📖 E lexova mesazhin.", "📖 Read the message.")

    gjendje_te_reja, mosha_e_re = lexo_profilin_nga_teksti(mesazh)
    gjendje_te_reja -= profili.gjendjet
    # Mosha te mesazhi ("djali 5 vjeç") ka përparësi: zakonisht tregon kush është pacienti.
    profili = Profili(mosha=mosha_e_re if mosha_e_re is not None else profili.mosha,
                      gjendjet=profili.gjendjet | gjendje_te_reja, shenime=profili.shenime)
    shenim = _shenim_profili(gjendje_te_reja, mosha_e_re)
    baza = dict(gjendje_te_reja=gjendje_te_reja, mosha_e_re=mosha_e_re, pa_doza=profili.femije)
    s_kont = _emrat(merr_simptomat_sipas_id(kont.simptomat)) if kont.simptomat else ""

    # 3. bisedë e thjeshtë
    if not shenim and (q := qellimi_bisedes(mesazh)):
        if q == "faleminderit" and s_kont:
            tekst = _zgjidh(FALEMINDERIT_ME_KONTEKST, historia).format(s=s_kont)
        elif q == "pohim" and s_kont:
            tekst = _zgjidh(POHIM_ME_KONTEKST, historia).format(s=s_kont)
        else:
            tekst = _zgjidh({"pershendetje": TE_PERSHENDETJES, "si_je": SI_JE, "faleminderit": FALEMINDERIT,
                             "mirupafshim": MIRUPAFSHIM, "kush_je": KUSH_JE, "pohim": POHIM}[q], historia)
        return Pergjigje(tekst=tekst, qellimi=q, **baza)

    # 4. përgjigje e pyetjes sqaruese
    simptomat, kandidatet = [], []
    t_norm = standardizo(mesazh)
    shto = bool(kont.simptomat and re.search(SHTESE, t_norm))  # "kam edhe kollë"
    if kont.pritje:
        simptomat = _zgjidh_pritjen(mesazh, kont.pritje)
        shto = shto or bool(simptomat and kont.pritje_shto)
    # 5. ilaç me emër
    if not simptomat and (permendura := gjej_barnat_e_permendura(mesazh)):
        return Pergjigje(tekst=shenim + pergjigje_per_ilacin(permendura, profili), qellimi="ilac",
                         barnat_konteksti=[r["b"]["id"] for r in permendura[:2]], **baza)
    # 6. simptomë e re
    if not simptomat:
        m.hap(f"🔎 Po kërkoj në bazën e njohurive ({_numri_frazave()} fraza, edhe me variantin standard)...",
              f"🔎 Searching the knowledge base ({_numri_frazave()} phrases)...")
        simptomat, kandidatet = kerko_simptomat(mesazh)
        if m.aktiv and _vlen_te_mendosh(t_norm, simptomat, kandidatet, kont, mesazh):
            simptomat, kandidatet = _mendo_per_simptomat(mesazh, historia, simptomat, kandidatet, m)
    vijues = qellimi_vijues(mesazh)
    grupi = _pyetje_grupi(mesazh, simptomat)
    if grupi:
        simptomat = [s for s in simptomat if s["id"] not in grupi[0]]

    if simptomat:
        ids = [s["id"] for s in simptomat]
        if vijues == "info" and not shenim:
            return Pergjigje(tekst=_vijuese_info(simptomat, historia), qellimi="info", simptomat=simptomat, **baza)
        if shto and not set(ids) & set(kont.simptomat):
            ids = (kont.simptomat + ids)[:MAKS_SIMPTOMA_BASHKE]
            simptomat = merr_simptomat_sipas_id(ids)
        perseritje = ids == kont.simptomat and not shenim
        m.hap("💊 Po kontrolloj ilaçet për profilin tënd (mosha, gjendjet, kundërindikimet)...",
              "💊 Checking the medicines against your profile (age, conditions, contraindications)...")
        barnat, perjashtuara = merr_barnat(ids, profili.te_gjitha_gjendjet())
        if perjashtuara:
            m.hap(f"⛔ Hoqa {len(perjashtuara)} ilaçe që nuk janë të sigurta për profilin tënd.",
                  f"⛔ Removed {len(perjashtuara)} medicines that are not safe for your profile.")
        tekst = shenim + pergjigje_standarde(simptomat, barnat, perjashtuara, profili, historia, perseritje)
        pritje = []
        if grupi:
            pritje, pyetja = grupi
            tekst += f"\n\n❓ {pyetja}"
        return Pergjigje(tekst=tekst, simptomat=simptomat, barnat=barnat, te_perjashtuara=perjashtuara,
                         burime=kerko_ne_pdf(mesazh), qellimi="simptome", pritje=pritje,
                         barnat_konteksti=[b["id"] for b in barnat], **baza)

    # Fjalë e përgjithshme ("kollë", "sytë") ose disa simptoma po aq të afërta → pyet.
    if grupi:
        ids, pyetja = grupi
        return Pergjigje(tekst=shenim + pyetja, qellimi="sqarim", pritje=ids, pritje_shto=shto, **baza)
    if kandidatet:
        return Pergjigje(tekst=shenim + _pyetje_kandidatesh(kandidatet, historia), qellimi="sqarim",
                         pritje=[s["id"] for s in kandidatet], pritje_shto=shto, **baza)

    # 7. pyetje vijuese për temën e bisedës
    if kont.simptomat or kont.barnat:
        simptomat = merr_simptomat_sipas_id(kont.simptomat) if kont.simptomat else []
        if shenim and simptomat:
            # Info e re për profilin ("jam shtatzënë") → rillogarit barnat për të njëjtat simptoma.
            barnat, perjashtuara = merr_barnat(kont.simptomat, profili.te_gjitha_gjendjet())
            return Pergjigje(tekst=shenim + pergjigje_standarde(simptomat, barnat, perjashtuara, profili, historia),
                             simptomat=simptomat, barnat=barnat, te_perjashtuara=perjashtuara, qellimi="profil",
                             barnat_konteksti=[b["id"] for b in barnat], **baza)
        if vijues == "doza" and (tekst := _vijuese_doza(kont, profili, historia)):
            return Pergjigje(tekst=tekst, qellimi="doza", barnat_konteksti=kont.barnat, **baza)
        if simptomat and vijues == "alternativa":
            tekst, barnat, perjashtuara, _ = _vijuese_alternativa(kont, profili, historia)
            return Pergjigje(tekst=tekst, barnat=barnat, te_perjashtuara=perjashtuara, qellimi="alternativa",
                             barnat_konteksti=[b["id"] for b in barnat] or kont.barnat, **baza)
        if simptomat and vijues == "keshilla":
            return Pergjigje(tekst=_vijuese_keshilla(simptomat, historia), qellimi="keshilla", **baza)
        if simptomat and vijues == "mjeku":
            return Pergjigje(tekst=_vijuese_mjeku(simptomat, historia), qellimi="mjeku", **baza)
        if simptomat and vijues == "info":
            return Pergjigje(tekst=_vijuese_info(simptomat, historia), qellimi="info", **baza)
        if simptomat and re.search(PYETJE, t_norm):
            return _pergjigje_llm(mesazh, historia, profili, simptomat, kont, baza, m)

    if shenim:
        return Pergjigje(tekst=shenim + "Tani më trego çfarë simptome ke.", qellimi="profil", **baza)
    # 8. ankesë e panjohur
    if m.pyetje:  # modeli mendoi dhe ka një pyetje sqaruese të saktë për këtë mesazh
        return Pergjigje(tekst="Dua të sigurohem që të kuptoj saktë: " + m.pyetje, qellimi="sqarim", **baza)
    if re.search(ANKESE_SIMPTOME, t_norm):
        return Pergjigje(tekst=_zgjidh(NUK_E_NJOH, historia), qellimi="e_panjohur", **baza)
    return Pergjigje(tekst=_zgjidh(SQARIM, historia), qellimi="sqarim", **baza)


RE_DOZE = re.compile(r"\d+([.,]\d+)?\s*(mg|ml|mcg|g\b|gram|tablet|kapsul|cop|pik|her[eë] n[eë] dit)", re.I)
ZEVENDESIM_DOZE = "_(Dozën e saktë e ke te kartat më poshtë dhe te fletëudhëzuesi.)_"


def pastro_dozat(tekst: str, barnat: list[dict]) -> str:
    """Rregulli 'pa doza nga modeli' zbatohet në kod: rreshtat me doza numerike (përveç emrave të ilaçeve,
    p.sh. 'Ibuprofen 200/400 mg') zëvendësohen me një referencë te kartat."""
    emrat = sorted({b["emer"] for b in barnat}, key=len, reverse=True)
    rreshta = []
    for rresht in tekst.split("\n"):
        pa_emra = rresht
        for e in emrat:
            pa_emra = pa_emra.replace(e, "")
        rreshta.append(ZEVENDESIM_DOZE if RE_DOZE.search(pa_emra) else rresht)
    return "\n".join(r for i, r in enumerate(rreshta) if r != ZEVENDESIM_DOZE or rreshta[i - 1:i] != [r])


def _pergjigje_llm(mesazh, historia, profili, simptomat, kont, baza, m: Mendimi | None = None) -> Pergjigje:
    """Pyetje vijuese e lirë: modeli gjuhësor përgjigjet, por vetëm me kontekstin nga databaza."""
    gjendjet = profili.te_gjitha_gjendjet()
    ids = [s["id"] for s in simptomat]
    barnat, perjashtuara = merr_barnat(ids, gjendjet)
    pdf = kerko_ne_pdf(mesazh)
    gjendjet_emra = [r["emer"] for r in query(
        "MATCH (g:Gjendje) WHERE g.id IN $ids RETURN g.emer AS emer", ids=sorted(gjendjet))]
    konteksti = _konteksti(profili, gjendjet_emra, simptomat, barnat, perjashtuara, pdf, profili.femije)
    anglisht = bool(m and m.gjuha == "en")
    mesazhet = [{"role": "system", "content": SYSTEM_PROMPT + (
        "\n\nIMPORTANT: the person writes in English. Write your whole answer in clear English "
        "(the context below is in Albanian; translate what you use)." if anglisht else "")}]
    mesazhet += [{"role": m["role"], "content": m["content"]} for m in historia[-6:]]
    mesazhet.append({"role": "user",
                     "content": f"KONTEKSTI NGA DATABAZA:\n{konteksti}\n\nPYETJA: {mesazh}"})
    try:
        if m and m.aktiv:
            m.hap("🧠 Po mendoj për pyetjen, vetëm me të dhënat nga databaza...",
                  "🧠 Thinking about the question, using only data from the database...")
            pergjigja, _ = chat_mendo(mesazhet, on_mendim=m.mendim)
            pergjigja = re.sub(r"<think>.*?</think>", "", pergjigja, flags=re.S).strip()
            m.hap("✅ Kontrollova përgjigjen: dozat me numra hiqen, ilaçet vijnë vetëm nga lista.",
                  "✅ Checked the answer: numeric doses are removed, medicines come only from the list.")
        else:
            pergjigja = chat(mesazhet)
        tekst = pastro_dozat(pergjigja, barnat)
    except Exception:
        tekst = ("Nuk e përpunova dot këtë pyetje tani. Mund të më pyesësh për dozën, alternativat, "
                 "këshillat ose kur duhet mjeku, ose pyet farmacistin.")
    return Pergjigje(tekst=tekst, simptomat=simptomat, barnat=barnat, te_perjashtuara=perjashtuara,
                     burime=pdf, qellimi="llm", ne_anglisht=anglisht, barnat_konteksti=kont.barnat or [b["id"] for b in barnat], **baza)
