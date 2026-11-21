"""Zgjerimi 2 i bazës së njohurive (data/njohurite.json):
  - fraza të reja për simptomat ekzistuese (gegërisht, pa ë/ç, fjalë të përditshme)
  - fjalë kyçe më të plota
  - barna të reja pa recetë dhe emra tregtarë shtesë
  - simptoma/sëmundje të reja të jetës së përditshme

Skripti është idempotent: mund të ekzekutohet disa herë pa krijuar dublikata.
Pas tij:  python ngarko_grafin.py
"""
import json
import re

from config import ROOT, normalizo

SKEDARI = ROOT / "data" / "njohurite.json"

# ---------------------------------------------------------------- fraza shtesë për simptomat ekzistuese
FRAZA_SHTESE = {
    "dhimbje_koke": ["më dhemb kryet", "me dhemb koka", "kam kokëdhimbje", "më pëlcet koka", "më dhemb koka nga stresi",
                     "dhimbje koke nga lodhja", "më rrah koka", "më dhemb koka prej mëngjesit", "migrenë me të përziera"],
    "dhimbje_dhembi": ["me dhemb dhembi", "më dhemb dhâmbi", "dhëmbi i pjekur", "më dhemb dhëmbi i pjekurisë",
                       "më dhemb dhëmbi kur pi ujë të ftohtë", "më janë skuqur mishrat", "më gjakosen mishrat e dhëmbëve",
                       "më është ënjtur faqja nga dhëmbi"],
    "temperature": ["kam zjarrmi", "kam ethe dhe dridhje", "me eshte ngritur temperatura", "jam me 38",
                    "kam temperaturë të lartë", "më nxehet trupi", "kam temperaturë që nga dje", "ethet nuk më ulen"],
    "grip_ftohje": ["jam i ftohur", "me ka zene gripi", "kam simptoma gripi", "më dhemb i gjithë trupi dhe jam ftohur",
                    "kam covid", "jam me korona", "më ka kapur një virozë", "kam ftohje dhe rrufë", "jam ftohur keq"],
    "dhimbje_fyti": ["më dhemb gurmazi", "me dhemb fyti", "kam faringjit", "kam angjinë", "më djeg gurmazi",
                     "kam tonsilit", "më dhemb fyti kur flas", "fyti më është tharë dhe më dhemb"],
    "kolle_thate": ["kollë e thatë natën", "kolle e thate", "kollitem gjithë natën pa nxjerrë", "kollë që më kruan fytin",
                    "kollë e thatë pas gripit", "kollitje e thatë"],
    "kolle_gelbaze": ["kolle me gelbaze", "nxjerr sekrecione kur kollitem", "kollë e rëndë me gëlbazë",
                      "kollë me flegmë", "më mblidhet gëlbaza në gjoks", "gëlbazë në fyt"],
    "bllokim_hunde": ["me ka zene hunda", "hundë e zënë", "kam hundë të bllokuar natën", "më pikon hunda",
                      "më rrjedh hunda si ujë", "nuk marr frymë dot nga hundët", "kam rrufë të fortë", "më dhemb balli nga sinusi"],
    "alergji": ["kam alergji nga pluhuri", "alergji nga macja", "teshtitje të shpeshta", "më kruhet hunda dhe teshtij",
                "alergji sezonale", "me lotojne syte", "teshtij çdo mëngjes", "jam alergjik nga poleni"],
    "kruajtje_lekure": ["më ha lëkura", "me kruhet lekura", "më ha trupi", "më ka pickuar mizë", "më pickoi një insekt",
                        "kam pickime mushkonjash", "më doli skuqje që kruhet", "më kruhet krahu", "më kruhet shumë natën",
                        "u dogja nga hithra"],
    "kerpudha_lekure": ["kerpudha ne kembe", "më kruhet mes gishtave", "kam kërpudha në ijë", "lëkurë e bardhë dhe e lagësht mes gishtave",
                        "më zhvishet lëkura e këmbëve", "njolla që kruhen në lëkurë"],
    "urth": ["kam gastrit", "me djeg stomaku", "më vjen acid në gojë", "djegie pas buzës së gjoksit", "më djeg gjoksi pasi ha",
             "kam thartira", "stomaku më djeg natën", "kam tretje të keqe"],
    "diarre": ["më shkon barku", "kam barkqitje", "barku i lirë", "me ka prishur barku", "kam diarre prej 2 ditësh",
               "jashtëqitje e ujshme", "diarre pas një ushqimi të prishur", "fëmija ka diarre"],
    "kapsllek": ["kam bark të zënë", "kapsllek", "nuk dal dot jashtë", "kam vështirësi për të dalë jashtë",
                 "jam kapsllëk prej ditësh", "jashtëqitje e fortë dhe me dhimbje"],
    "fryrje_gazra": ["kam gaze", "barku më është fryrë si top", "fryhem pas ngrënies", "kam fryrje", "me fryhet barku"],
    "dhimbje_barku": ["me dhemb barku", "më përdridhen zorrët", "më dhemb stomaku", "kam dhimbje barku",
                      "më ther barku", "ngërçe në zorrë"],
    "dhimbje_menstruale": ["më dhemb barku nga regjimi", "dhimbje gjatë periodës", "kam periodën dhe më dhemb",
                           "dhimbje menstruacionesh", "më dhemb mesi nga cikli"],
    "dhimbje_muskulore": ["më dhemb krahu", "më dhemb supi", "më dhemb bryli", "më dhembin kockat", "kam artrozë",
                          "më dhembin nyjet", "u mavijosa", "më dhemb kyçi i dorës", "më dhembin këmbët", "u ndrydha në dorë",
                          "kam ngurtësi në qafë", "më dhemb qafa nga gjumi"],
    "dhimbje_shpine": ["më dhemb kurrizi", "me dhemb shpina", "më dhemb shpina në mes", "më ka kapur mesi",
                       "dhimbje në shpinë kur ngrihem", "më dhemb shpina nga puna", "dhimbje lumbare"],
    "nauze_te_vjella": ["më vjen për me vjellë", "me perzihet", "kam të vjella prej mëngjesit", "vjell gjithçka që ha",
                        "ndihem i përzier", "më vjen të vjell"],
    "semundje_udhetimi": ["më bëhet keq në makinë", "me perzihet ne makine", "sëmundje deti", "fëmijës i bëhet keq në makinë",
                          "më përzihet në aeroplan", "kam frikë se do vjell në udhëtim"],
    "dhimbje_veshi": ["me dhemb veshi", "më dhembin veshët", "më ther veshi", "më dhemb veshi natën",
                      "më bubullon veshi", "otit"],
    "pagjumesi": ["s'po më merr gjumi", "nuk me ze gjumi", "nuk më merr gjumi natën", "zgjohem herët dhe s'fle dot",
                  "kam gjumë të çrregullt", "fle keq"],
    "afte_gojore": ["kam afte ne goje", "më ka dalë një plagë në gojë", "plagë e bardhë në gojë", "më djeg goja nga një plagë",
                    "plagë në buzë nga brenda"],
    "herpes_labial": ["më doli herpesi", "kam flluskë në buzë", "kam ftohje në buzë", "më ka dalë uzbek në buzë"],
    "hemorroide": ["kam hemoroide", "më del gjak kur shkoj jashtë", "dhimbje në anus", "më kruhet anusi", "kam majasëll të fryrë"],
    "sy_te_thate": ["me thahen syte", "sytë më djegin", "sy të lodhur nga telefoni", "më djegin sytë në fund të ditës",
                    "më duket sikur kam rërë në sy"],
    "konjuktivit_alergjik": ["sy te kuq", "më janë skuqur sytë dhe më kruhen", "sytë e kuq nga alergjia",
                             "më kruhen sytë nga poleni"],
    "akne": ["kam puçrra", "më dalin puçrra në ballë", "pucrra ne fytyre", "kam akne në shpinë", "puçërr e madhe në fytyrë"],
    "djegie_lekure": ["u dogja me vaj", "më dogji dielli shpatullat", "u dogja nga dielli", "djegie e lehtë në dorë",
                      "u dogja me tenxhere", "më është skuqur lëkura nga dielli"],
    "plage_e_vogel": ["u preva me thike", "kam një plagë të vogël", "u gërvishta në dorë", "më çau lëkurën macja",
                      "u preva duke rruar", "gërvishtje në gju"],
    "morra": ["vajza ka morra", "djali ka morra në flokë", "morra në kokë", "fëmija solli morra nga shkolla"],
    "zbokth": ["kam zbokth në flokë", "më bien luspa nga koka", "zbokth", "lëkura e kokës më kruhet dhe zhvishet"],
    "kandidoze_vaginale": ["kam kandidoze", "kruajtje në vaginë", "rrjedhje e bardhë si gjizë", "infeksion vaginal me kërpudha"],
    "cistit": ["më djeg kur bëj pipi", "me djeg kur urinoj", "kam infeksion në urinë", "urinoj shpesh dhe pak",
               "më therr kur urinoj", "infeksion i fshikëzës"],
    "marramendje": ["më merret mendja", "më vjen mendja rrotull", "me merren mendte", "kam marramendje kur ngrihem",
                    "më turbullohet kur ngrihem"],
    "lodhje": ["jam i këputur", "jam i dërrmuar", "jam pa takat", "ndihem i lodhur gjithë kohën", "jam shumë e lodhur"],
    "krimba": ["djali ka krimba", "kruajtje në anus natën te fëmija", "fëmija ka parazitë", "krimba të vegjël të bardhë"],
    "lenie_duhani": ["dua të heq cigaren", "dua të lë cigaret", "si ta lë duhanin", "pi një paketë në ditë dhe dua ta lë",
                     "dua të ndaloj duhanin"],
    "lekure_e_thate": ["më thahet lëkura", "lekure e thate", "kam lëkurë të ashpër", "lëkura më plasaritet në dimër",
                       "më janë çarë duart"],
    "lytha_kallo": ["kam lytha", "kam kallo në gisht të këmbës", "lyth në shputë", "lëkurë e fortë në thembër"],
    "kerpudha_thonjsh": ["thonjtë më janë verdhur", "kerpudha ne thonj", "thoi më është trashur dhe zverdhur"],
    "gjakderdhje_hunde": ["më rrjedh gjak nga hundët", "me rrjedh gjak nga hunda", "fëmijës i rrjedh gjak nga hunda",
                          "më del gjak nga hunda kur fryj"],
    "humbje_zeri": ["më ka rënë zëri", "nuk më del zëri", "me eshte ngjirur zeri", "zëri më është ngjirur nga të bërtiturat"],
    "ere_goje": ["me vjen ere goja", "goja më mban erë", "erë e keqe nga goja në mëngjes"],
    "dehidratim_vape": ["më ka goditur dielli", "goditje nga dielli", "kam pirë pak ujë dhe ndihem keq", "jam dehidratuar nga diarreja",
                        "më ka rënë të fikët nga vapa"],
    "ankth_stres": ["jam nervoz", "ndihem i shqetësuar", "kam stres në punë", "jam me ankth", "zemra më rreh nga stresi",
                    "kam merak dhe s'qetësohem"],
}

# ---------------------------------------------------------------- fjalë kyçe të reja (zëvendësojnë të vjetrat)
FJALE_KYCE = {
    "dhimbje_koke": r"\bkok(a|e|en|es)\b|\bkrye(t|ni|n)?\b|migren|\bball(i|e)\b|temth",
    "dhimbje_dhembi": (r"(?<!dalin )(?<!dalja e )(?<!dalje e )\bdhemb(i|et|e|eve)\b|\bdhamb(i|et|e)?\b|dhemball|"
                       r"nofull|mishrat e dhembe|mishrat\w*( \w+){0,2} (gjakos|skuq|enjt)|pjekuris"),
    "temperature": r"temperatur|\bethe(t)?\b|febr|zjarrm",
    "grip_ftohje": r"\bgrip|ftohur|ftohje(?! ne buz)|viroz|\bcovid|korona",
    "dhimbje_fyti": r"\bfyt|bajame|gellt|gurmaz|faringjit|tonsilit|angjin",
    "kolle_gelbaze": r"\b(me|nxjerr|kam) gelbaz|gelbaz|sekrecion|kolle e lageshte|flegm",
    "alergji": r"alergj|teshtij|teshtim|teshtit|polen|lotojne syte|kruhen syte|syte\w* (me )?(lotojne|kruhen)",
    "kruajtje_lekure": (r"kruh\w* (e |me )?lekur|lekur\w*( \w+){0,2} kruh|pick|mushkonj|urtikar|skuqje (e |ne )?lekur|"
                        r"kruajtje|me ha (lekura|trupi|krahu|kemba|dora)|hithr|me kruhet (trupi|krahu|kemba|dora)"),
    "urth": r"\burth|thartir|refluks|djeg\w* (\w+ )?stomak|stomak\w* (me )?djeg|\bacid|gastrit|tretje (e |te )?(keqe|veshtire)",
    "diarre": (r"diarre|jashteqitje (te |e )?(lengshme|ujshme)|prishur barku|barkqitj|bark(u)? (i |te )?lir|"
               r"me shkon barku"),
    "kapsllek": (r"kapsllek|kapllek|bark\w* (i |te )?(zene|mbyllur)|(nuk|s') ?(shkoj|dal) dot (ne tualet|jashte)|"
                 r"jashteqitje (e |te )?fort"),
    "fryrje_gazra": r"gazra|\bgaze\b|fryr\w* (e )?bark|bark\w* (i |me )?fry|fryhet barku|fryhem|meteoriz",
    "dhimbje_barku": r"\bbark|\bstomak|ngerc(?!\w* (ne |te |e )?(kemb|pulp|kofsh|dor|duar|gisht))|spazm|kollik|zorr",
    "dhimbje_menstruale": r"menstru|\bcikl|perjodi|\bperiod|dismenorre|regjim",
    "dhimbje_muskulore": (r"muskuj|\bkyc|\bgjur|ndrydh|perdredh|mavijos|\bkrah|\bkemb|\bqaf|\bsup(i|et|in)?\b|"
                          r"\bbryl|\bkock|\bnyj|artroz|artrit|reumat|tendin|ngurtesi"),
    "dhimbje_shpine": r"\bshpin|\bmes(i|in)\b|lumbag|lumbar|kurriz",
    "dhimbje_veshi": r"\bvesh(i|in|et|ve)?\b|otit",
    "pagjumesi": (r"pagjum|insomn|(nuk|s')( ?po)?( ?me)? (ze|merr)( dot)? gjum|fle dot|(nuk|s') fle\b|zgjohem (shpesh|naten|heret)|"
                  r"nuk fle mire|fle keq|gjume (te |i )?crregull"),
    "cistit": (r"djeg\w* (kur|gjate|ne) (urin|bej pipi)|urin\w* (me )?djeg|urinoj (shume )?shpesh|cistit|infeksion\w*( \w+){0,2} urin|"
               r"fshikez|pipi|therr\w* (kur|gjate) urin"),
    "marramendje": r"marramendj|merren mendt|merret mendja|mendja( me)? (vjen )?rrotull|vjen rrotull|sillet (bota|koka)|vertigo|turbullohet",
    "lodhje": r"\blodh(ur|je)\b(?! (e |te )?sy)|pa energji|pa fuqi|ndihem i dobet|keputur|dermuar|pa takat",
    "dehidratim_vape": r"dehidrat|\bvape|pike (e )?diell|goditur dielli|goditje (nga |e )?diell|\betje",
    "ankth_stres": r"ankth|\bstres|nervoz|\bpanik|merak|shqetesuar",
    "lenie_duhani": r"duhan|cigar|nikotin",
    "herpes_labial": r"herpes|fllusk\w* (ne |te |rreth )?(buz|goj)|ftohje ne buz|uzbek",
}

# ---------------------------------------------------------------- emra tregtarë shtesë
EMRA_SHTESE = {
    "paracetamol": ["Paracetamol Profarma", "Tylenol"],
    "ibuprofen": ["Ibuprofen Profarma", "Advil"],
    "aspirine": ["Aspirin C", "Aspirina"],
    "loratadine": ["Clarityn"],
    "oksimetazoline": ["Afrin"],
    "kripe_fiziologjike": ["Quixx", "Humer"],
    "omeprazol": ["Omeprazol Profarma", "Ultop"],
    "dekstrometorfan": ["Sinecod (butamirat, i ngjashëm)"],
    "ambroksol": ["Bronchopront", "Ambrolan"],
    "diklofenak_xhel": ["Diclac gel", "Olfen gel"],
    "pastile_fyti": ["Septolete", "Faringosept", "Mebucaine"],
    "simetikone": ["Sab Simplex", "Disflatyl"],
    "butilskopolamine": ["Buscol"],
    "antacid": ["Talcid", "Gastal"],
}

# ---------------------------------------------------------------- barna të reja
BARNA_TE_REJA = [
    {
        "id": "benzidamine_sprej", "emer": "Benzidaminë 0,15% sprej/shpëlarës për fytin", "lende_aktive": "Benzidaminë",
        "forma": "Sprej goje ose shpëlarës", "emra_tregtare": ["Tantum Verde", "Benzydamine", "Difflam"],
        "doza": "Sprej: 4–8 spërkatje në fyt 2–6 herë në ditë. Shpëlarës: 15 ml për 20–30 sekonda, 2–3 herë në ditë (mos e gëlltit).",
        "doza_maks": "Jo më shumë se 6 herë në ditë.",
        "kohezgjatja": "Pa mjek jo më shumë se 7 ditë.",
        "si_merret": "Pas ngrënies. Mos ha e mos pi për 15–20 minuta pas përdorimit.",
        "paralajmerime": ["Mund të japë mpirje ose djegie të lehtë në gojë.",
                          "Nëse dhimbja e fytit zgjat mbi 7 ditë ose ke temperaturë të lartë, shko te mjeku."],
        "efekte_anesore": ["Mpirje ose djegie në gojë", "Rrallë: skuqje lëkure, spazmë bronkesh"],
        "kunderindikime": {},
        "kujdes": {"astme": "Rrallë mund të shkaktojë spazmë të bronkeve: përdore me kujdes.",
                   "shtatzeni": "Pyet farmacistin ose mjekun para përdorimit.",
                   "femije_nen_12": "Sprej mund të përdoret nga 6 vjeç me dozë më të ulët; pyet farmacistin."},
    },
    {
        "id": "acetilcisteine", "emer": "Acetilcisteinë 600 mg (për gëlbazë të trashë)", "lende_aktive": "Acetilcisteinë",
        "forma": "Tableta shkumëzuese ose pluhur", "emra_tregtare": ["ACC 600", "Fluimucil", "NAC"],
        "doza": "600 mg një herë në ditë, ose 200 mg 3 herë në ditë.",
        "doza_maks": "Jo më shumë se 600 mg në 24 orë.",
        "kohezgjatja": "Pa mjek jo më shumë se 5–7 ditë.",
        "si_merret": "Tretet në një gotë ujë dhe pihet pas ushqimit. Pi shumë lëngje gjatë ditës. Mos e merr vonë në mbrëmje.",
        "paralajmerime": ["Mos e kombino me barna që ndalojnë kollën (p.sh. dekstrometorfan): gëlbaza mbetet në mushkëri.",
                          "Antibiotikët merri 2 orë larg acetilcisteinës."],
        "efekte_anesore": ["Të përziera, urth, diarre", "Rrallë: reaksione alergjike, spazmë bronkesh"],
        "kunderindikime": {"nen_2": "Nuk përdoret te fëmijët nën 2 vjeç."},
        "kujdes": {"astme": "Mund të shkaktojë spazmë të bronkeve te astmatikët.",
                   "ulcer": "Me ulçerë përdore me kujdes: mund ta irritojë stomakun.",
                   "shtatzeni": "Konsultohu me mjekun para përdorimit.", "gjidhenie": "Konsultohu me mjekun.",
                   "femije_nen_12": "Për fëmijë ka forma dhe doza të veçanta: pyet farmacistin."},
    },
    {
        "id": "hedera_shurup", "emer": "Shurup me ekstrakt gjethesh urthi (Hedera helix)", "lende_aktive": "Ekstrakt i thatë i gjetheve të urthit",
        "forma": "Shurup", "emra_tregtare": ["Prospan", "Hedelix", "Bronchipret"],
        "doza": "Të rriturit: 5–7,5 ml 2–3 herë në ditë (shiko fletëudhëzuesin e produktit).",
        "doza_maks": "Mos e kalo dozën ditore të shkruar në paketim.",
        "kohezgjatja": "Pa mjek jo më shumë se 1 javë.",
        "si_merret": "Me ose pa ushqim. Tunde shishen para përdorimit.",
        "paralajmerime": ["Nëse ke vështirësi në frymëmarrje, temperaturë ose gëlbazë me gjak, shko te mjeku."],
        "efekte_anesore": ["Të përziera, diarre", "Rrallë: reaksione alergjike"],
        "kunderindikime": {"nen_2": "Nuk përdoret te fëmijët nën 2 vjeç (rrezik për rrugët e frymëmarrjes)."},
        "kujdes": {"astme": "Me astmë pyet mjekun para përdorimit.", "shtatzeni": "Pyet mjekun ose farmacistin.",
                   "gjidhenie": "Pyet mjekun ose farmacistin.",
                   "femije_nen_12": "Për fëmijë doza është më e vogël: pyet farmacistin.",
                   "diabet": "Disa shurupe kanë sheqer: kontrollo paketimin."},
    },
    {
        "id": "mentol_balsam", "emer": "Balsam me mentol dhe eukalipt (për fërkim në gjoks)", "lende_aktive": "Mentol, kamfor, vaj eukalipti",
        "forma": "Pomadë", "emra_tregtare": ["Vicks VapoRub", "Pectoral balsam"],
        "doza": "Fërko një sasi të vogël në gjoks dhe shpinë deri në 3 herë në ditë.",
        "doza_maks": "Jo më shumë se 3 herë në ditë.",
        "kohezgjatja": "Pa mjek jo më shumë se 5–7 ditë.",
        "si_merret": "Vetëm në lëkurë të paprekur. Mos e vendos në hundë, gojë ose në plagë. Laj duart pas përdorimit.",
        "paralajmerime": ["Mos e gëlltit: kamfori është helmues.", "Mbaje larg syve."],
        "efekte_anesore": ["Irritim i lëkurës", "Rrallë: kollë ose spazmë nga avujt"],
        "kunderindikime": {"nen_2": "Kamfori dhe mentoli mund të shkaktojnë probleme në frymëmarrje te fëmijët nën 2 vjeç."},
        "kujdes": {"astme": "Avujt e mentolit mund të shkaktojnë krizë astme.",
                   "epilepsi": "Kamfori mund të ulë pragun e krizave.", "shtatzeni": "Pyet farmacistin."},
    },
    {
        "id": "vitamine_d", "emer": "Vitaminë D3 1000 IU", "lende_aktive": "Kolekalciferol",
        "forma": "Tableta, kapsula ose pika", "emra_tregtare": ["Vigantol", "Devit", "D3 1000 IU"],
        "doza": "1000 IU (25 mikrogram) një herë në ditë.",
        "doza_maks": "Pa mjek jo më shumë se 4000 IU në ditë.",
        "kohezgjatja": "Mund të merret gjatë dimrit ose afatgjatë; mjeku mund të kontrollojë nivelin në gjak.",
        "si_merret": "Pas vaktit kryesor (përthithet më mirë me yndyrë).",
        "paralajmerime": ["Mos merr disa produkte me vitaminë D njëkohësisht (multivitamina e kanë shpesh).",
                          "Dozat e larta afatgjata mund të rrisin kalciumin në gjak."],
        "efekte_anesore": ["Në doza të larta: të përziera, etje, kapsllëk, gurë në veshka"],
        "kunderindikime": {},
        "kujdes": {"veshka": "Me sëmundje veshkash ose gurë në veshka konsultohu me mjekun.",
                   "femije_nen_12": "Fëmijët kanë doza të veçanta (zakonisht pika): pyet pediatrin."},
    },
    {
        "id": "vitamine_c", "emer": "Vitaminë C 500 mg", "lende_aktive": "Acid askorbik",
        "forma": "Tableta ose tableta shkumëzuese", "emra_tregtare": ["Cevit", "Redoxon", "Vitamin C 500"],
        "doza": "500–1000 mg në ditë.",
        "doza_maks": "Jo më shumë se 2000 mg në ditë.",
        "kohezgjatja": "Mund të merret disa javë; ushqimi (frutat, perimet) mbetet burimi më i mirë.",
        "si_merret": "Me ose pas ushqimit.",
        "paralajmerime": ["Dozat e larta mund të shkaktojnë diarre dhe gurë në veshka.",
                          "Tabletat shkumëzuese kanë natrium: kujdes me tensionin."],
        "efekte_anesore": ["Diarre, urth ose dhimbje barku në doza të larta"],
        "kunderindikime": {},
        "kujdes": {"veshka": "Me gurë ose sëmundje veshkash mos kalo 500 mg në ditë pa mjek.",
                   "hipertension": "Tabletat shkumëzuese kanë kripë (natrium); zgjidh tabletat e zakonshme."},
    },
    {
        "id": "zink", "emer": "Zink 10–25 mg", "lende_aktive": "Glukonat ose sulfat zinku",
        "forma": "Tableta ose pastila", "emra_tregtare": ["Zinkorot", "Zinc 25", "Zincovit"],
        "doza": "10–25 mg zink në ditë. Te ftohja: pastila zinku që nga dita e parë.",
        "doza_maks": "Jo më shumë se 40 mg zink në ditë.",
        "kohezgjatja": "Te ftohja 5–7 ditë; si suplement jo më shumë se disa javë pa mjek.",
        "si_merret": "Pas ushqimit (me stomak bosh të përzien).",
        "paralajmerime": ["Antibiotikët (tetraciklinë, ciprofloksacinë) dhe hekuri merren të paktën 2 orë larg zinkut.",
                          "Përdorimi i gjatë në doza të larta ul bakrin në trup."],
        "efekte_anesore": ["Të përziera, shije metalike"],
        "kunderindikime": {},
        "kujdes": {"femije_nen_12": "Fëmijët kanë doza më të vogla: pyet farmacistin."},
    },
    {
        "id": "multivitamine", "emer": "Multivitaminë me minerale", "lende_aktive": "Vitamina dhe minerale të kombinuara",
        "forma": "Tableta", "emra_tregtare": ["Centrum", "Supradyn", "Pharmaton", "Berocca"],
        "doza": "1 tabletë në ditë.",
        "doza_maks": "1 tabletë në ditë. Mos e kombino me vitamina të tjera pa pyetur.",
        "kohezgjatja": "1–3 muaj, pastaj pushim; ushqimi i larmishëm mbetet më i rëndësishmi.",
        "si_merret": "Në mëngjes pas ushqimit.",
        "paralajmerime": ["Mbaje larg fëmijëve: hekuri në multivitamina është i rrezikshëm për ta në sasi të mëdha.",
                          "Urina mund të ngjyroset e verdhë: është normale."],
        "efekte_anesore": ["Të përziera, shije e keqe, kapsllëk (nga hekuri)"],
        "kunderindikime": {},
        "kujdes": {"shtatzeni": "Në shtatzëni përdor vetëm multivitamina për shtatzëni (pa shumë vitaminë A).",
                   "antikoagulante": "Vitamina K mund të ndikojë te varfarina: pyet mjekun.",
                   "veshka": "Me sëmundje veshkash pyet mjekun.", "tiroide": "Levotiroksina merret 4 orë larg multivitaminës."},
    },
    {
        "id": "hekur", "emer": "Hekur (sulfat/fumarat hekuri) për mungesë hekuri", "lende_aktive": "Hekur dyvalent",
        "forma": "Tableta ose shurup", "emra_tregtare": ["Ferro-Gradumet", "Tardyferon", "Ferrum Lek", "Maltofer"],
        "doza": "Zakonisht 1 tabletë (60–100 mg hekur) në ditë, ose çdo dy ditë sipas mjekut.",
        "doza_maks": "Sipas mjekut; mos e kalo dozën e paketimit.",
        "kohezgjatja": "Zakonisht 3 muaj; mjeku kontrollon gjakun.",
        "si_merret": "Me stomak bosh me ujë ose lëng portokalli. Jo me çaj, kafe ose qumësht (2 orë larg).",
        "paralajmerime": ["Mungesa e hekurit duhet konfirmuar me analizë gjaku para se të marrësh hekur.",
                          "Mbaje larg fëmijëve: mbidoza e hekurit është e rrezikshme për ta.",
                          "Jashtëqitja bëhet e zezë: është normale."],
        "efekte_anesore": ["Kapsllëk, të përziera, dhimbje barku", "Jashtëqitje e zezë"],
        "kunderindikime": {},
        "kujdes": {"ulcer": "Hekuri irriton stomakun: me ulçerë pyet mjekun.",
                   "tiroide": "Levotiroksina merret 4 orë larg hekurit.",
                   "femije_nen_12": "Fëmijët kanë doza sipas peshës: vetëm sipas pediatrit."},
    },
    {
        "id": "acid_folik", "emer": "Acid folik 0,4 mg", "lende_aktive": "Acid folik",
        "forma": "Tableta", "emra_tregtare": ["Folacin", "Acid folik 0,4 mg", "Folio"],
        "doza": "0,4 mg (400 mikrogram) një herë në ditë.",
        "doza_maks": "Pa mjek jo më shumë se 1 mg në ditë.",
        "kohezgjatja": "Nga të paktën 1 muaj para shtatzënisë deri në javën e 12-të të shtatzënisë.",
        "si_merret": "Çdo ditë në të njëjtën orë, me ose pa ushqim.",
        "paralajmerime": ["Me epilepsi, diabet ose kur je mbipeshë mjeku mund të japë dozë më të lartë (5 mg)."],
        "efekte_anesore": ["Rrallë: të përziera, fryrje"],
        "kunderindikime": {},
        "kujdes": {"epilepsi": "Disa barna kundër epilepsisë ndërveprojnë me acidin folik: pyet mjekun."},
    },
    {
        "id": "magnez", "emer": "Magnez 300 mg", "lende_aktive": "Citrat ose oksid magnezi",
        "forma": "Tableta, kapsula ose pluhur", "emra_tregtare": ["Magnesium Verla", "Magne B6", "Magnerot"],
        "doza": "300 mg në ditë (në 1–2 doza).",
        "doza_maks": "Jo më shumë se 350 mg magnez suplement në ditë pa mjek.",
        "kohezgjatja": "2–4 javë; nëse ngërçet vazhdojnë, shko te mjeku.",
        "si_merret": "Pas ushqimit, mundësisht në mbrëmje.",
        "paralajmerime": ["Antibiotikët dhe barnat për osteoporozë merren 2 orë larg magnezit.",
                          "Në doza të larta jep diarre."],
        "efekte_anesore": ["Diarre, dhimbje barku"],
        "kunderindikime": {"veshka": "Me sëmundje veshkash magnezi grumbullohet në gjak dhe mund të jetë i rrezikshëm."},
        "kujdes": {"femije_nen_12": "Pyet farmacistin për dozën te fëmijët."},
    },
    {
        "id": "probiotik", "emer": "Probiotik (Saccharomyces boulardii ose Lactobacillus)", "lende_aktive": "Mikroorganizma probiotike",
        "forma": "Kapsula ose qeskë", "emra_tregtare": ["Enterol", "Linex", "Bioflorin", "Lactogermina"],
        "doza": "1 kapsulë/qeskë 1–2 herë në ditë (sipas produktit).",
        "doza_maks": "Sipas paketimit.",
        "kohezgjatja": "Gjatë diarresë dhe disa ditë pas saj; me antibiotik, gjatë kurës dhe 1 javë pas.",
        "si_merret": "Me ujë jo të nxehtë. Merre 2–3 orë larg antibiotikut.",
        "paralajmerime": ["Probiotiku nuk zëvendëson rehidratimin: te diarreja pi shumë lëngje ose ORS."],
        "efekte_anesore": ["Fryrje e lehtë në ditët e para"],
        "kunderindikime": {"imunitet": "Me imunitet të dobët ose kateter venoz, rrallë mund të shkaktojë infeksion në gjak."},
        "kujdes": {},
    },
    {
        "id": "glicerine_supozitor", "emer": "Supozitor glicerine", "lende_aktive": "Glicerinë",
        "forma": "Supozitor (për të rritur dhe për fëmijë)", "emra_tregtare": ["Glycerin supp", "Supposte Glicerina"],
        "doza": "1 supozitor sipas nevojës, 1 herë në ditë.",
        "doza_maks": "1 herë në ditë.",
        "kohezgjatja": "Për raste të rastësishme; jo çdo ditë për më shumë se 1 javë pa mjek.",
        "si_merret": "Lagu me ujë dhe vendose në anus. Vepron brenda 15–30 minutave.",
        "paralajmerime": ["Nëse kapsllëku zgjat mbi 2 javë ose ka gjak, shko te mjeku."],
        "efekte_anesore": ["Djegie e lehtë në anus"],
        "kunderindikime": {},
        "kujdes": {"femije_nen_12": "Për fëmijë ka supozitorë më të vegjël (pediatrikë)."},
    },
    {
        "id": "senna", "emer": "Senna (laksativ bimor)", "lende_aktive": "Sennozidë A dhe B",
        "forma": "Tableta ose çaj", "emra_tregtare": ["Senokot", "Laxatan", "X-Prep"],
        "doza": "7,5–15 mg sennozidë në mbrëmje para gjumit.",
        "doza_maks": "Jo më shumë se 30 mg në ditë.",
        "kohezgjatja": "Pa mjek jo më shumë se 1 javë.",
        "si_merret": "Para gjumit me ujë; vepron pas 8–12 orësh.",
        "paralajmerime": ["Përdorimi i gjatë e dobëson zorrën dhe ul kaliumin.",
                          "Mos e përdor me dhimbje të fortë barku pa ditur shkakun."],
        "efekte_anesore": ["Ngërçe barku", "Urina mund të ngjyroset kuqërremtë"],
        "kunderindikime": {"femije_nen_12": "Nuk përdoret te fëmijët nën 12 vjeç pa mjek."},
        "kujdes": {"shtatzeni": "Në shtatzëni zgjidh më parë makrogol ose laktulozë.", "gjidhenie": "Pyet mjekun.",
                   "zemra": "Ulja e kaliumit është e rrezikshme me disa barna të zemrës."},
    },
    {
        "id": "oksid_zinku_krem", "emer": "Pastë me oksid zinku (për skuqje pelenash)", "lende_aktive": "Oksid zinku",
        "forma": "Pastë ose krem", "emra_tregtare": ["Sudocrem", "Desitin", "Bepanthen Baby (dekspantenol)", "Pastë zinku"],
        "doza": "Shtresë e hollë në lëkurë të pastër dhe të thatë në çdo ndërrim pelene.",
        "doza_maks": "Sa herë që nevojitet.",
        "kohezgjatja": "Nëse skuqja nuk përmirësohet për 3 ditë, shko te pediatri.",
        "si_merret": "Pastro dhe thaje mirë lëkurën para se ta vendosësh.",
        "paralajmerime": ["Mos e vendos në plagë të hapura ose me qelb."],
        "efekte_anesore": ["Shumë rrallë: irritim"],
        "kunderindikime": {},
        "kujdes": {},
    },
    {
        "id": "permetrine_krem", "emer": "Permetrinë 5% krem (për zgjebe)", "lende_aktive": "Permetrinë",
        "forma": "Krem", "emra_tregtare": ["Lyclear", "Permethrin 5%", "Infectoscab"],
        "doza": "Vendose në të gjithë trupin nga qafa deri te gishtat e këmbëve, lëre 8–12 orë dhe pastaj lahu. Përsërite pas 7 ditësh.",
        "doza_maks": "Zakonisht 30 g për të rritur për një aplikim.",
        "kohezgjatja": "2 aplikime me 7 ditë diferencë. Kruajtja mund të zgjasë edhe 2–4 javë pas trajtimit.",
        "si_merret": "Mbrëmjeve në lëkurë të ftohtë e të thatë. Mos harro mes gishtave, nën thonj dhe në organet gjenitale.",
        "paralajmerime": ["Trajtohet e gjithë familja dhe personat që jetojnë bashkë në të njëjtën ditë.",
                          "Rrobat dhe çarçafët lahen në 60 °C ose mbyllen në qese për 3 ditë.",
                          "Mbaje larg syve dhe gojës."],
        "efekte_anesore": ["Djegie, kruajtje ose skuqje e përkohshme"],
        "kunderindikime": {},
        "kujdes": {"nen_2": "Te foshnjat vetëm sipas mjekut (përfshin edhe kokën dhe fytyrën).",
                   "shtatzeni": "Mund të përdoret, por konsultohu me mjekun.", "gjidhenie": "Lahe kremin nga gjiri para ushqyerjes.",
                   "femije_nen_12": "Doza është më e vogël: pyet farmacistin."},
    },
    {
        "id": "heparinoid_xhel", "emer": "Heparinë xhel (për mavijosje dhe këmbë të rënda)", "lende_aktive": "Heparinë natriumi ose heparinoid",
        "forma": "Xhel", "emra_tregtare": ["Lioton 1000", "Hirudoid", "Contractubex (për shenja)"],
        "doza": "Fërko 3–10 cm xhel në zonë 1–3 herë në ditë.",
        "doza_maks": "3 herë në ditë.",
        "kohezgjatja": "Pa mjek jo më shumë se 10 ditë.",
        "si_merret": "Vetëm në lëkurë të paprekur, jo në plagë të hapura ose në mukoza.",
        "paralajmerime": ["Ënjtje e njëanshme e këmbës me dhimbje dhe nxehtësi mund të jetë trombozë: shko menjëherë te mjeku."],
        "efekte_anesore": ["Rrallë: skuqje lëkure"],
        "kunderindikime": {},
        "kujdes": {"antikoagulante": "Nëse merr barna hollimi gjaku dhe të dalin mavijosje pa shkak, fol me mjekun."},
    },
    {
        "id": "aloe_xhel", "emer": "Xhel me aloe vera (pas diellit)", "lende_aktive": "Aloe vera",
        "forma": "Xhel", "emra_tregtare": ["Aloe Vera Gel", "After Sun", "Panthenol After Sun"],
        "doza": "Vendose në lëkurë disa herë në ditë.",
        "doza_maks": "Sa herë që nevojitet.",
        "kohezgjatja": "Derisa lëkura të qetësohet (zakonisht 2–5 ditë).",
        "si_merret": "Mbaje në frigorifer: i ftohtë qetëson më shumë.",
        "paralajmerime": ["Mos e vendos në flluska të çara ose plagë të hapura."],
        "efekte_anesore": ["Rrallë: alergji"],
        "kunderindikime": {},
        "kujdes": {},
    },
    {
        "id": "repelent", "emer": "Repelent kundër mushkonjave dhe rriqrave (DEET ose ikaridinë)", "lende_aktive": "DEET 20–50% ose ikaridinë 20%",
        "forma": "Sprej ose losion", "emra_tregtare": ["Autan", "OFF!", "Moskito Guard"],
        "doza": "Shtresë e hollë në lëkurën e zbuluar; përsërite sipas paketimit (zakonisht çdo 4–8 orë).",
        "doza_maks": "Sipas paketimit.",
        "kohezgjatja": "Për sa kohë je në rrezik pickimi.",
        "si_merret": "Kremi i diellit vihet i pari, repelenti pas 20 minutash. Mos e sprucit në fytyrë: vendose me dorë.",
        "paralajmerime": ["Mbaje larg syve, gojës dhe plagëve.", "Lahu kur kthehesh brenda."],
        "efekte_anesore": ["Irritim i lëkurës ose i syve"],
        "kunderindikime": {},
        "kujdes": {"nen_2": "Te foshnjat nën 2 muaj nuk përdoret; te fëmijët e vegjël përdor përqendrim të ulët (DEET ≤ 30%).",
                   "shtatzeni": "Ikaridina ose DEET në përqendrim të ulët konsiderohen të sigurta; pyet farmacistin.",
                   "femije_nen_12": "Zgjidh produkte për fëmijë dhe vendose ti në duart e fëmijës, jo ai vetë."},
    },
    {
        "id": "pika_veshi_dylle", "emer": "Pika veshi për zbutjen e dyllit", "lende_aktive": "Karbamid peroksid 6,5% ose vaj ulliri/bajameje",
        "forma": "Pika veshi", "emra_tregtare": ["Otex", "Cerumol", "A-Cerumen", "Vaj ulliri"],
        "doza": "3–5 pika në veshin e bllokuar 2 herë në ditë.",
        "doza_maks": "2 herë në ditë.",
        "kohezgjatja": "3–5 ditë. Nëse veshi mbetet i bllokuar, mjeku e lan veshin.",
        "si_merret": "Shtrihu anash, hidh pikat dhe qëndro 5 minuta në atë pozicion.",
        "paralajmerime": ["Mos përdor pika nëse ke dhimbje të fortë, rrjedhje nga veshi ose daulle të shpuar.",
                          "Mos fut shkopinj pambuku në vesh: e shtyjnë dyllin më thellë."],
        "efekte_anesore": ["Ndjesi fërgëllimë ose ulje e përkohshme e dëgjimit"],
        "kunderindikime": {},
        "kujdes": {"femije_nen_12": "Te fëmijët pyet pediatrin para përdorimit."},
    },
    {
        "id": "plaster_hidrokoloid", "emer": "Leukoplast hidrokoloid për flluska", "lende_aktive": "Hidrokoloid",
        "forma": "Leukoplast", "emra_tregtare": ["Compeed", "Hansaplast Blister", "Leukoplast"],
        "doza": "Një leukoplast mbi flluskë; lëre derisa të bjerë vetë (disa ditë).",
        "doza_maks": "Sipas nevojës.",
        "kohezgjatja": "Derisa flluska të shërohet.",
        "si_merret": "Lëkura duhet të jetë e pastër dhe e thatë. Mos e ço flluskën.",
        "paralajmerime": ["Me diabet, flluskat në këmbë duhet t'i shohë mjeku ose infermieri."],
        "efekte_anesore": ["Shumë rrallë: irritim nga ngjitësi"],
        "kunderindikime": {},
        "kujdes": {"diabet": "Me diabet plagët e këmbëve shërohen më ngadalë: kontrollo çdo ditë dhe fol me mjekun."},
    },
    {
        "id": "klorur_alumini", "emer": "Antidjersë me klorur alumini 15–20%", "lende_aktive": "Klorur alumini heksahidrat",
        "forma": "Roll-on ose sprej", "emra_tregtare": ["Driclor", "Etiaxil", "Perspirex", "Odaban"],
        "doza": "Në mbrëmje në lëkurë të thatë, çdo natë derisa djersitja të ulet, pastaj 1–2 herë në javë.",
        "doza_maks": "1 herë në ditë.",
        "kohezgjatja": "Afatgjatë sipas nevojës.",
        "si_merret": "Mbrëmjeve, në lëkurë plotësisht të thatë; lahet në mëngjes. Jo menjëherë pas rruajtjes.",
        "paralajmerime": ["Mos e vendos në lëkurë të irrituar ose të çarë."],
        "efekte_anesore": ["Djegie ose kruajtje e lëkurës"],
        "kunderindikime": {},
        "kujdes": {"veshka": "Me sëmundje të rëndë veshkash pyet mjekun para produkteve me alumin."},
    },
    {
        "id": "minoksidil", "emer": "Minoksidil 5% (për rënien e flokëve)", "lende_aktive": "Minoksidil",
        "forma": "Losion ose shkumë", "emra_tregtare": ["Regaine", "Rogaine", "Alopexy"],
        "doza": "1 ml në lëkurën e thatë të kokës 2 herë në ditë (gratë: 5% 1 herë në ditë ose 2% 2 herë).",
        "doza_maks": "2 ml në ditë.",
        "kohezgjatja": "Rezultatet duken pas 3–6 muajsh; kur ndërpritet, flokët bien sërish.",
        "si_merret": "Vetëm në lëkurën e kokës, laj duart pas përdorimit. Mos e lag kokën për 4 orë.",
        "paralajmerime": ["Në javët e para rënia e flokëve mund të shtohet përkohësisht.",
                          "Rënie e papritur ose me njolla e flokëve duhet parë nga mjeku."],
        "efekte_anesore": ["Kruajtje e lëkurës së kokës", "Rrallë: rrahje zemre, marramendje, qime në fytyrë"],
        "kunderindikime": {"shtatzeni": "Nuk përdoret në shtatzëni.", "gjidhenie": "Nuk përdoret gjatë gjidhënies.",
                           "nen_16": "Nuk përdoret nën 18 vjeç."},
        "kujdes": {"zemra": "Me sëmundje zemre pyet mjekun: mund të shpejtojë rrahjet.",
                   "hipertension": "Me tension të lartë pyet mjekun para përdorimit."},
    },
    {
        "id": "vazeline", "emer": "Vazelinë / balsam buzësh", "lende_aktive": "Vazelinë e bardhë, dyll",
        "forma": "Pomadë ose stik", "emra_tregtare": ["Vaseline", "Labello", "Blistex", "Bepanthen (dekspantenol)"],
        "doza": "Shtresë e hollë disa herë në ditë dhe para gjumit.",
        "doza_maks": "Sa herë që nevojitet.",
        "kohezgjatja": "Sipas nevojës.",
        "si_merret": "Në buzë ose lëkurë të thatë e të çarë.",
        "paralajmerime": ["Mos e vendos brenda hundës te personat që marrin oksigjen."],
        "efekte_anesore": ["Shumë rrallë: alergji"],
        "kunderindikime": {},
        "kujdes": {},
    },
]

# Barna të reja që shtohen te simptomat ekzistuese (në fund të listës, ruhet rendi i parë).
BARNA_PER_SIMPTOMAT = {
    "dhimbje_fyti": ["benzidamine_sprej"],
    "afte_gojore": ["benzidamine_sprej"],
    "kolle_gelbaze": ["acetilcisteine", "hedera_shurup"],
    "kolle_thate": ["hedera_shurup"],
    "grip_ftohje": ["zink", "mentol_balsam"],
    "bllokim_hunde": ["mentol_balsam"],
    "diarre": ["probiotik"],
    "kapsllek": ["glicerine_supozitor", "senna"],
    "dhimbje_muskulore": ["heparinoid_xhel"],
    "djegie_lekure": ["aloe_xhel"],
    "lekure_e_thate": ["vazeline"],
    "lodhje": ["multivitamine"],
}

# ---------------------------------------------------------------- simptoma të reja
SIMPTOMA_TE_REJA = [
    {
        "id": "mungese_vitaminash", "emer": "Vitamina dhe forcim imuniteti",
        "pershkrim": "Pyetje për vitamina, minerale dhe për të forcuar organizmin, p.sh. në dimër ose kur sëmuresh shpesh.",
        "fraza": ["dua vitamina", "çfarë vitamina të marr", "dua të forcoj imunitetin", "sëmurem shpesh", "vitaminë D",
                  "vitamin c", "më duhen vitamina për dimër", "multivitaminë", "kam mungesë vitamine D", "dua zink"],
        "barnat": ["vitamine_d", "vitamine_c", "zink", "multivitamine"],
        "shenja_alarmi": ["Sëmuresh shumë shpesh ose infeksionet nuk kalojnë (mund të ketë shkak tjetër)",
                          "Lodhje e madhe, humbje peshe pa shkak ose djersë natën",
                          "Dhimbje kockash ose dobësi muskujsh e vazhdueshme"],
        "keshilla": ["Ushqim i larmishëm: fruta, perime, peshk, vezë, bishtajore.", "Fli 7–9 orë dhe lëviz çdo ditë.",
                     "15–20 minuta diell në ditë ndihmojnë për vitaminën D.", "Mos merr disa suplemente njëkohësisht pa pyetur farmacistin."],
        "fjale_kyce": r"vitamin|multivitamin|forcoj imunitet|forcim (i )?imunitet|semurem (shume )?shpesh|\bzink",
        "info": "Shumica e njerëzve me ushqim të larmishëm nuk kanë nevojë për shumë suplemente. Vitamina D mungon shpesh në dimër "
                "dhe te ata që dalin pak në diell; vitamina C dhe zinku mund ta shkurtojnë pak ftohjen.",
        "kerkon_mjek": False,
    },
    {
        "id": "anemi_hekur", "emer": "Mungesë hekuri / anemi", "kerkon_mjek": True,
        "pershkrim": "Lodhje, zbehje dhe hemoglobinë e ulët nga mungesa e hekurit.",
        "fraza": ["kam anemi", "kam mungesë hekuri", "hemoglobina e ulët", "më ka dalë hekuri i ulët", "ferritina e ulët",
                  "jam i zbehtë dhe i lodhur", "dua hekur", "kam gjak të pakët"],
        "barnat": ["hekur", "vitamine_c"],
        "shenja_alarmi": ["Gulçim, rrahje të shpejta zemre ose të fikët", "Jashtëqitje e zezë ose me gjak, ose menstruacione shumë të rënda",
                          "Humbje peshe pa shkak", "Anemi në shtatzëni ose te fëmijët"],
        "keshilla": ["Ha mish të kuq, mëlçi, bishtajore, spinaq dhe vezë.", "Vitamina C (portokall, limon) ndihmon përthithjen e hekurit.",
                     "Çaji dhe kafja pas ngrënies ulin përthithjen: pi 1–2 orë më vonë."],
        "fjale_kyce": r"\banemi|hekur|hemoglobin|ferritin|gjak (te |i )?pak|zbeht",
        "info": "Anemia nga mungesa e hekurit vjen shpesh nga menstruacionet e rënda, shtatzënia ose ushqimi i varfër, por mund të jetë "
                "edhe shenjë gjakderdhjeje në stomak ose zorrë. Prandaj duhet konfirmuar me analizë dhe shkaku duhet gjetur nga mjeku.",
    },
    {
        "id": "ngerce_kembesh", "emer": "Ngërçe në këmbë", "kerkon_mjek": False,
        "pershkrim": "Tkurrje e papritur dhe me dhimbje e muskujve të pulpës ose këmbës, shpesh natën.",
        "fraza": ["më mblidhen këmbët natën", "kam ngërç në pulpë", "ngërçe në këmbë", "më kap ngërçi natën",
                  "më tërhiqet muskuli i këmbës", "kram në këmbë", "më mpihen dhe më mblidhen këmbët", "ngërç në gishtat e këmbës"],
        "barnat": ["magnez"],
        "shenja_alarmi": ["Këmba e ënjtur, e kuqe, e nxehtë dhe me dhimbje (mund të jetë trombozë)",
                          "Dobësi ose mpirje e vazhdueshme e këmbës",
                          "Ngërçe shumë të shpeshta pas fillimit të një bari të ri (p.sh. diuretik)"],
        "keshilla": ["Shtrije muskulin: tërhiq gishtat e këmbës drejt vetes.", "Masazho dhe ngroh muskulin.",
                     "Pi mjaft ujë, sidomos në vapë ose pas sportit.", "Bëj shtrirje të lehta para gjumit."],
        "fjale_kyce": r"ngerc\w*( \w+){0,2} (kemb|pulp|kofsh|gisht)|(kemb|pulp)\w*( \w+){0,3} ngerc|\bkram|me mblidhen (kembet|muskujt)|\bpulp",
        "info": "Ngërçet e këmbëve janë të zakonshme, sidomos natën, pas sportit, në shtatzëni dhe te të moshuarit. "
                "Zakonisht kalojnë vetë pas disa minutash.",
    },
    {
        "id": "dalje_dhembesh", "emer": "Dalja e dhëmbëve te foshnja", "kerkon_mjek": False,
        "pershkrim": "Foshnja është e mërzitur, jargavitet dhe kafshon gjëra kur i dalin dhëmbët.",
        "fraza": ["po i dalin dhëmbët foshnjës", "beba po nxjerr dhëmbë", "i dalin dhëmbët", "dalja e dhëmbëve",
                  "foshnja kafshon gjithçka dhe qan", "djalit të vogël i dalin dhëmbët", "jargavitet shumë dhe i dalin dhëmbët"],
        "barnat": [],
        "shenja_alarmi": ["Temperaturë mbi 38 °C (dalja e dhëmbëve nuk jep temperaturë të lartë)", "Foshnja nën 3 muaj me temperaturë: urgjencë",
                          "Diarre, të vjella ose refuzon të pijë", "Qan pa pushim dhe nuk qetësohet"],
        "keshilla": ["Jepi unazë dhëmbësh të ftohtë (jo të ngrirë) ose një pecetë të lagur e të ftohtë.",
                     "Fërkoji lehtë mishin e dhëmbëve me gisht të pastër.", "Fshi jargët shpesh që të mos skuqet lëkura.",
                     "Për dhimbje: paracetamol ose ibuprofen në formë shurupi për fëmijë, me dozë sipas peshës; pyet farmacistin ose pediatrin."],
        "fjale_kyce": r"dalin dhembet|dalja e dhembeve|dalje (e )?dhembeve|nxjerr dhembe|dhembe(t)? (e )?(pare|qumeshtit)",
        "info": "Dhëmbët e parë dalin zakonisht nga 6 muaj deri në 2–3 vjeç. Foshnja mund të jetë nervoze, të jargavitet dhe të ketë "
                "temperaturë pak të ngritur, por temperatura e lartë ose diarreja vijnë nga shkaqe të tjera.",
    },
    {
        "id": "skuqje_pelenash", "emer": "Skuqje nga pelenat", "kerkon_mjek": False,
        "pershkrim": "Lëkurë e kuqe dhe e irrituar në zonën e pelenës te foshnja.",
        "fraza": ["foshnja ka skuqje nga pelena", "skuqje pelenash", "beba është skuqur te pelena", "i është skuqur prapanica bebes",
                  "irritim nga pelenat", "djali i vogël është skuqur poshtë"],
        "barnat": ["oksid_zinku_krem", "dekspantenol_krem"],
        "shenja_alarmi": ["Flluska, plagë të hapura ose qelb", "Temperaturë ose foshnja duket e sëmurë",
                          "Skuqje e kuqe e ndezur me pika anash (mund të jetë kërpudhë)", "Nuk përmirësohet pas 3 ditësh"],
        "keshilla": ["Ndërro pelenën shpesh dhe sapo të laget.", "Lëre foshnjën pa pelenë disa minuta në ditë.",
                     "Pastro me ujë të ngrohtë; shmang letrat e lagura me parfum.", "Thaje lëkurën duke e prekur lehtë, jo duke fërkuar."],
        "fjale_kyce": r"pelen|skuq\w*( \w+){0,2} (bebe|beba|foshnj)",
        "info": "Skuqja e pelenave vjen nga lagështia, urina dhe jashtëqitja që irritojnë lëkurën. Me ndërrim të shpeshtë dhe një pastë "
                "mbrojtëse zakonisht kalon brenda 2–3 ditësh.",
    },
    {
        "id": "zgjebe", "emer": "Zgjebe", "kerkon_mjek": False,
        "pershkrim": "Kruajtje e fortë, sidomos natën, me kokrriza të vogla mes gishtave, në kyçe, bel ose organe gjenitale.",
        "fraza": ["kam zgjebe", "zgjebe", "më kruhet shumë natën mes gishtave", "e gjithë familja kruhet", "skabie",
                  "kokrriza që kruhen mes gishtave të duarve"],
        "barnat": ["permetrine_krem", "loratadine"],
        "shenja_alarmi": ["Plagë me qelb ose temperaturë (infeksion)", "Kruajtja nuk ulet 4 javë pas trajtimit",
                          "Lëkurë e trashë me kore (zgjebe e rëndë)", "Te foshnjat nën 2 muaj"],
        "keshilla": ["Trajto të gjithë njerëzit e shtëpisë në të njëjtën ditë.", "Lahi rrobat, peshqirët dhe çarçafët në 60 °C.",
                     "Mos e ndaj krevatin ose peshqirin derisa të përfundojë trajtimi.", "Është mirë që mjeku ta konfirmojë diagnozën."],
        "fjale_kyce": r"zgjeb|skabie|scabies",
        "info": "Zgjebja shkaktohet nga një parazit shumë i vogël që hyn në lëkurë. Ngjitet me kontakt të gjatë lëkurë me lëkurë, "
                "prandaj trajtohet e gjithë familja njëkohësisht.",
    },
    {
        "id": "dylle_veshi", "emer": "Dyll në vesh (vesh i zënë)", "kerkon_mjek": False,
        "pershkrim": "Vesh i bllokuar nga dylli, me dëgjim më të ulët, pa dhimbje të fortë.",
        "fraza": ["kam dyll në vesh", "më është zënë veshi nga dylli", "tapë dylli në vesh", "nuk dëgjoj mirë nga një vesh",
                  "dyll veshi", "më duket veshi i mbyllur pas dushit"],
        "barnat": ["pika_veshi_dylle"],
        "shenja_alarmi": ["Dhimbje e fortë, temperaturë ose rrjedhje nga veshi", "Humbje e papritur e dëgjimit",
                          "Marramendje ose zhurmë e vazhdueshme në vesh", "Ke pasur daulle të shpuar ose operacion në vesh"],
        "keshilla": ["Mos përdor shkopinj pambuku brenda veshit.", "Pika vaji ulliri për disa ditë e zbutin dyllin.",
                     "Nëse veshi mbetet i bllokuar pas 5 ditësh, mjeku ose infermieri e lan."],
        "fjale_kyce": r"\bdyll|cerumen|tap\w* (e |dylli )?(ne |te )?vesh",
        "info": "Dylli e mbron veshin dhe zakonisht del vetë. Kur grumbullohet, zbutet me pika dhe vetëm rrallë duhet larje te mjeku.",
    },
    {
        "id": "venat_kembe", "emer": "Këmbë të rënda dhe vena varikoze", "kerkon_mjek": False,
        "pershkrim": "Rëndim, lodhje ose ënjtje e lehtë e të dyja këmbëve në mbrëmje, venat e dukshme.",
        "fraza": ["kam këmbë të rënda", "më ënjten këmbët në mbrëmje", "kam variçe", "vena varikoze", "më rëndohen këmbët nga qëndrimi",
                  "më fryhen kyçet e këmbëve nga vapa", "kam venat e fryra në këmbë"],
        "barnat": ["heparinoid_xhel"],
        "shenja_alarmi": ["Vetëm njëra këmbë e ënjtur, e kuqe, e nxehtë dhe me dhimbje (trombozë): shko menjëherë te mjeku",
                          "Gulçim ose dhimbje në gjoks bashkë me ënjtjen: telefono 127/112",
                          "Ënjtje e të dyja këmbëve me gulçim ose shtim peshe (zemra ose veshkat)", "Plagë në këmbë që nuk shërohen"],
        "keshilla": ["Ngri këmbët mbi nivelin e zemrës kur pushon.", "Ec çdo ditë dhe mos qëndro gjatë në këmbë ose ulur pa lëvizur.",
                     "Çorape kompresive (nga farmacia) ndihmojnë shumë.", "Shmang vapën e madhe, saunën dhe këpucët me taka."],
        "fjale_kyce": r"varic|varikoz|\bvenat|kemb\w* (te |e )?rend|enjt\w*( \w+){0,2} kemb|kemb\w*( \w+){0,2} (enjt|fryh)|me enjten kembet",
        "info": "Këmbët e rënda vijnë shpesh nga qëndrimi i gjatë në këmbë, vapa, shtatzënia ose venat e dobësuara. "
                "Ënjtja e njërës këmbë me dhimbje ndryshon: duhet parë menjëherë.",
    },
    {
        "id": "mbrojtje_insekte", "emer": "Mbrojtje nga mushkonjat dhe rriqrat", "kerkon_mjek": False,
        "pershkrim": "Si të mbrohesh nga pickimet e mushkonjave dhe rriqrave, dhe çfarë të bësh kur të kap një rriqër.",
        "fraza": ["si të mbrohem nga mushkonjat", "repelent për mushkonja", "më ka kapur një rriqër", "kam një rriqër në lëkurë",
                  "si ta heq rriqrën", "dua diçka kundër mushkonjave", "sprej kundër insekteve"],
        "barnat": ["repelent"],
        "shenja_alarmi": ["Pas pickimit të rriqrës: temperaturë, dhimbje trupi ose gjakderdhje nga mishrat/hunda (shko menjëherë te mjeku)",
                          "Rreth i kuq që zgjerohet rreth pickimit të rriqrës (sëmundja e Lyme)",
                          "Ënjtje e fytyrës, buzëve ose vështirësi në frymëmarrje pas pickimit: urgjencë 127/112"],
        "keshilla": ["Rriqrën hiqe me piskatore, afër lëkurës, duke tërhequr ngadalë drejt lart pa e shtrydhur.",
                     "Mos e djeg dhe mos vendos vaj ose alkool mbi rriqrën.", "Pas heqjes pastro me antiseptik dhe shëno datën.",
                     "Vish rroba të gjata, me ngjyrë të çelët, dhe kontrollo trupin pas shëtitjeve në bar.",
                     "Përdor rrjeta në dritare dhe hiq ujin e ndenjur rreth shtëpisë."],
        "fjale_kyce": r"repelent|rriq|mbroh\w*( \w+){0,2} (mushkonj|insekt)|kunder (mushkonj|insekt)",
        "info": "Mushkonjat dhe rriqrat mund të bartin sëmundje. Repelenti dhe rrobat mbrojtëse e ulin rrezikun; "
                "rriqra e hequr shpejt (brenda 24 orësh) e ul shumë rrezikun e infeksionit.",
    },
    {
        "id": "lemza", "emer": "Lemza (hik)", "kerkon_mjek": False,
        "pershkrim": "Kontraksione të papritura të diafragmës me zhurmë karakteristike.",
        "fraza": ["kam lemzë", "më ka zënë lemza", "nuk më ndalet lemza", "lemza", "kam hik", "kam lemzë prej orësh"],
        "barnat": [],
        "shenja_alarmi": ["Lemzë që zgjat më shumë se 48 orë", "Me dhimbje gjoksi, vështirësi në gëlltitje ose në frymëmarrje",
                          "Me të vjella ose humbje peshe"],
        "keshilla": ["Pi ngadalë një gotë ujë të ftohtë.", "Mbaj frymën 10–20 sekonda disa herë.", "Gëlltit një lugë sheqer.",
                     "Ha ngadalë dhe shmang pijet me gaz."],
        "fjale_kyce": r"lemz|\bhik\b",
        "info": "Lemza zakonisht kalon vetë brenda pak minutash. Shkaktohet nga ngrënia e shpejtë, pijet me gaz, alkooli ose emocionet.",
    },
    {
        "id": "djersitje", "emer": "Djersitje e tepërt", "kerkon_mjek": False,
        "pershkrim": "Djersë e shumtë nën sqetull, në duar ose në këmbë, edhe pa vapë apo sport.",
        "fraza": ["djersitem shumë", "kam djersitje të tepërt", "më djersijnë duart", "djersë nën sqetull", "më djersijnë këmbët",
                  "erë e keqe nga djersa"],
        "barnat": ["klorur_alumini"],
        "shenja_alarmi": ["Djersë natën që të lagin çarçafët, me temperaturë ose humbje peshe", "Djersitje e papritur me dhimbje gjoksi: urgjencë",
                          "Djersitje me dridhje, rrahje zemre ose humbje peshe (tiroide)"],
        "keshilla": ["Vish pambuk ose rroba sportive që thahen shpejt.", "Ndërro çorapet çdo ditë dhe alterno këpucët.",
                     "Antidjersa vihet në mbrëmje, jo në mëngjes.", "Shmang kafenë, alkoolin dhe ushqimet pikante."],
        "fjale_kyce": r"djers",
        "info": "Djersitja e tepërt (hiperhidrozë) është e zakonshme dhe zakonisht e padëmshme. Djersa natën me humbje peshe "
                "ose temperaturë kërkon kontroll.",
    },
    {
        "id": "renie_flokesh", "emer": "Rënie flokësh", "kerkon_mjek": False,
        "pershkrim": "Rënie e shtuar e flokëve ose rrallim gradual në krye.",
        "fraza": ["më bien flokët", "rënie flokësh", "po më rrallohen flokët", "po qeroset koka", "më bien flokët shumë kur lahem",
                  "po tullacem", "alopeci"],
        "barnat": ["minoksidil"],
        "shenja_alarmi": ["Rënie me njolla të rrumbullakëta pa flokë", "Rënie e madhe e papritur, me lodhje ose shtim/humbje peshe (tiroide, hekur)",
                          "Te gratë: me cikël të çrregullt, akne ose qime në fytyrë", "Lëkura e kokës e skuqur, me plagë ose dhimbje"],
        "keshilla": ["Rënia 50–100 fije në ditë është normale.", "Pas lindjes, stresit ose një sëmundjeje me temperaturë flokët bien 2–3 muaj dhe pastaj rriten vetë.",
                     "Ha mjaft proteina dhe kontrollo hekurin dhe tiroiden nëse rënia zgjat.", "Shmang bishtat shumë të shtrënguar dhe nxehtësinë e tepërt."],
        "fjale_kyce": r"(bien|renie|rrallo\w*)( \w+){0,2} flok|flok\w*( \w+){0,2} (bien|rrallo)|qeros|tullac|alopeci",
        "info": "Rënia e flokëve vjen shpesh nga trashëgimia, stresi, lindja, dietat e rrepta ose mungesa e hekurit. "
                "Minoksidili ndihmon te rrallimi trashëgues, por duhet përdorur vazhdimisht.",
    },
    {
        "id": "flluska_kembe", "emer": "Flluska nga këpucët", "kerkon_mjek": False,
        "pershkrim": "Flluskë me lëng në thembër ose gishta nga fërkimi i këpucëve.",
        "fraza": ["më vranë këpucët", "kam flluskë në thembër", "flluska nga këpucët e reja", "më doli flluskë në këmbë nga ecja",
                  "më ka çarë këpuca", "flluskë në gisht të këmbës"],
        "barnat": ["plaster_hidrokoloid", "povidon_jod"],
        "shenja_alarmi": ["Skuqje që zgjerohet, qelb, nxehtësi ose temperaturë (infeksion)", "Me diabet ose qarkullim të dobët të gjakut",
                          "Flluska pa shkak të dukshëm ose në shumë vende të trupit"],
        "keshilla": ["Mos e ço flluskën: lëkura sipër mbron nga infeksioni.", "Nëse çahet vetë, pastroje dhe mbuloje me leukoplast.",
                     "Vish çorape të thata dhe këpucë të provuara; këpucët e reja vishi pak nga pak."],
        "fjale_kyce": r"fllusk\w*( \w+){0,2} (kemb|themb|gisht|kepuc|ecj)|kepuc\w*( \w+){0,2} (vrane|fllusk|cari|cau)|me vrane kepucet",
        "info": "Flluskat nga fërkimi shërohen vetë brenda një jave nëse mbrohen nga fërkimi dhe nuk çohen.",
    },
    {
        "id": "buze_te_thata", "emer": "Buzë të thata dhe të çara", "kerkon_mjek": False,
        "pershkrim": "Buzë të thata, të plasaritura ose të çara në cepa, sidomos në dimër.",
        "fraza": ["më janë çarë buzët", "buzë të thata", "më plasariten buzët", "më thahen buzët", "çarje në cep të buzës",
                  "buzët më djegin nga i ftohti"],
        "barnat": ["vazeline", "dekspantenol_krem"],
        "shenja_alarmi": ["Plagë në buzë që nuk shërohet pas 3 javësh", "Flluska që djegin (mund të jetë herpes)",
                          "Çarje në cepat e buzës që nuk kalojnë (mund të jetë kërpudhë ose mungesë vitamine)"],
        "keshilla": ["Mos i lëpi buzët: i than më shumë.", "Pi ujë mjaftueshëm.", "Përdor balsam buzësh me mbrojtje nga dielli kur del jashtë.",
                     "Përdor lagështues ajri në dhomë në dimër."],
        "fjale_kyce": r"buz\w*( \w+){0,2} (that|plasarit|cahen|care|cara|djeg)|(care|carje|plasarit\w*|that\w*) (e |te |ne )?(cep \w+ )?buz",
        "info": "Buzët thahen nga i ftohti, era, dielli dhe lëpirja. Balsami i thjeshtë disa herë në ditë zakonisht mjafton.",
    },
    {
        "id": "konjuktivit_infektiv", "emer": "Sy me qelb (konjuktivit infektiv)", "kerkon_mjek": True,
        "pershkrim": "Sy i kuq me sekrecion të verdhë ose qepalla që ngjiten në mëngjes.",
        "fraza": ["më ngjiten sytë në mëngjes", "kam qelb në sy", "syri më nxjerr qelb", "sy i kuq me cipa",
                  "fëmija ka sy me qelb", "më del lëng i verdhë nga syri"],
        "barnat": ["lot_artificiale"],
        "shenja_alarmi": ["Dhimbje e fortë syri, ulje e shikimit ose ndjeshmëri e madhe ndaj dritës", "Te foshnjat nën 1 muaj",
                          "Përdor lente kontakti dhe syri është i kuq", "Nuk përmirësohet pas 3 ditësh"],
        "keshilla": ["Pastro sytë me garzë të lagur në ujë të zier e të ftohur, nga brenda jashtë, garzë e re për çdo sy.",
                     "Laj duart shpesh dhe mos e ndaj peshqirin.", "Mos përdor lente kontakti derisa të shërohesh."],
        "fjale_kyce": r"qelb\w*( \w+){0,2} sy|\bsy\w*( \w+){0,3} (qelb|ngjit|cipa)|ngjiten syte",
        "info": "Syri me qelb shkaktohet shpesh nga bakteret ose viruset dhe ngjitet lehtë. Pikat me antibiotik jepen me recetë, "
                "prandaj farmacisti ose mjeku duhet ta shohë.",
    },
    {
        "id": "planifikim_shtatzenie", "emer": "Planifikim shtatzënie (acid folik)", "kerkon_mjek": False,
        "pershkrim": "Përgatitja para shtatzënisë dhe në muajt e parë: acidi folik dhe kujdesi me barnat.",
        "fraza": ["dua të mbetem shtatzënë", "po planifikojmë një fëmijë", "acid folik", "çfarë duhet të marr para shtatzënisë",
                  "duam të bëjmë fëmijë", "sa acid folik duhet të marr"],
        "barnat": ["acid_folik"],
        "shenja_alarmi": ["Gjakderdhje vaginale ose dhimbje e fortë barku në fillim të shtatzënisë",
                          "Të vjella aq të shpeshta sa nuk mban dot as ujin",
                          "Merr barna për epilepsi, diabet, tension ose depresion: fol me mjekun para shtatzënisë"],
        "keshilla": ["Fillo acidin folik të paktën 1 muaj para shtatzënisë.", "Lëre duhanin dhe alkoolin.",
                     "Para çdo ilaçi të ri pyet farmacistin nëse je ose mund të jesh shtatzënë.",
                     "Bëj një kontroll te mjeku ose gjinekologu para shtatzënisë."],
        "fjale_kyce": r"acid folik|folik|mbetem shtatzen|planifik\w*( \w+){0,2} (femij|shtatzen|bebe)|(bejme|bej) (nje )?femij",
        "info": "Acidi folik para dhe në 12 javët e para të shtatzënisë ul shumë rrezikun e defekteve të shtyllës kurrizore te foshnja.",
    },
]


def _kontrollo_regex(id_, pattern, fraza):
    re.compile(pattern)
    assert not re.search(r"[ëçËÇA-Z]", pattern), f"{id_}: fjalë kyçe jo e normalizuar"
    kapur = [f for f in fraza if re.search(pattern, normalizo(f))]
    return len(kapur), len(fraza)


def main():
    data = json.loads(SKEDARI.read_text(encoding="utf-8"))
    simptomat = {s["id"]: s for s in data["simptomat"]}
    barnat = {b["id"]: b for b in data["barnat"]}

    for b in BARNA_TE_REJA:
        if b["id"] in barnat:
            barnat[b["id"]].update(b)
        else:
            data["barnat"].append(b)
            barnat[b["id"]] = b

    for bid, emra in EMRA_SHTESE.items():
        lista = barnat[bid]["emra_tregtare"]
        lista += [e for e in emra if e not in lista]

    for s in SIMPTOMA_TE_REJA:
        if s["id"] in simptomat:
            simptomat[s["id"]].update(s)
        else:
            data["simptomat"].append(s)
            simptomat[s["id"]] = s

    for sid, fraza in FRAZA_SHTESE.items():
        ekz = {normalizo(f) for f in simptomat[sid]["fraza"]}
        for f in fraza:
            if normalizo(f) not in ekz:
                simptomat[sid]["fraza"].append(f)
                ekz.add(normalizo(f))

    for sid, kw in FJALE_KYCE.items():
        simptomat[sid]["fjale_kyce"] = kw

    for sid, ids in BARNA_PER_SIMPTOMAT.items():
        lista = simptomat[sid]["barnat"]
        lista += [b for b in ids if b not in lista]

    # Kontroll: referenca, regex, gjendje
    gjendjet = {g["id"] for g in data["gjendjet"]}
    for b in data["barnat"]:
        for k in ("kunderindikime", "kujdes"):
            for g in b[k]:
                assert g in gjendjet, (b["id"], g)
    for s in data["simptomat"]:
        for bid in s["barnat"]:
            assert bid in barnat, (s["id"], bid)
        n, tot = _kontrollo_regex(s["id"], s["fjale_kyce"], s["fraza"])
        if n < tot:
            pa = [f for f in s["fraza"] if not re.search(s["fjale_kyce"], normalizo(f))]
            print(f"  ({s['id']}: fjalët kyçe kapin {n}/{tot}; pa kapur: {pa})")

    data["_shenim"] = ("Baza e njohurive për FarmaBot: barna pa recetë (OTC), simptoma, sëmundje të lehta dhe nevoja të përditshme "
                       "(vitamina, foshnja, lëkura, udhëtimi). Kontrollo dhe përditëso me një farmacist përpara përdorimit real.")
    SKEDARI.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gati: {len(data['barnat'])} barna, {len(data['simptomat'])} simptoma, "
          f"{sum(len(s['fraza']) for s in data['simptomat'])} fraza.")


if __name__ == "__main__":
    main()
