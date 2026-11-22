<p align="center"><img src="assets/ikona.png" width="120" alt="FarmaBot"></p>

# FarmaBot: chatbot farmacie (GraphRAG lokal)

Personi shkruan simptomat në shqip ose anglisht (p.sh. *"më dhemb dhëmbi"*) dhe chatbot-i sugjeron ilaçe pa recetë.
Ai heq barnat që nuk janë të sigurta për profilin e personit (moshë, shtatzëni, ulçerë, barna që merr...)
dhe tregon kur duhet shkuar te mjeku.

## 🖥️ Ndërfaqja web (stili ChatGPT / Claude)

Aplikacioni është web i plotë: server Python (Starlette + Uvicorn, `web/server.py`) dhe faqe HTML/CSS/JS
pa librari të jashtme (`web/static/`). Niset me `python -m web` → http://localhost:8501 (vetëm në këtë kompjuter).

| Pjesa | Çfarë bën |
|---|---|
| Paneli majtas | *Bisedë e re*, kërkim, lista e bisedave sipas datës (Sot, Dje, 7 ditët e fundit…), riemërto / shkarko / fshi |
| Butoni i panelit | e mbyll / hap panelin (edhe me **Ctrl+B**); gjendja mbahet në shfletues |
| Fusha e shkrimit | Enter dërgon, Shift+Enter rresht i ri; butoni **Mendo më thellë** ndez arsyetimin e modelit |
| Përgjigjja | hapat e mendimit (të mbyllshëm), teksti, kartat e ilaçeve, ilaçet e përjashtuara, kur duhet mjeku, fletëudhëzuesi FDA |
| Cilësimet | Tema (Sistemi / E bardhë / E zezë), Gjuha (Shqip / English), Profili shëndetësor, Llogaria |
| Paneli i adminit | Përmbledhje, Përdoruesit (rolet, fjalëkalimet, bisedat), Ilaçet (ndrysho / shto), Backup |

- **Gjuha** ndryshon të gjithë ndërfaqen dhe gjuhën e përgjigjeve: me *English* bota përgjigjet anglisht
  edhe kur pyetja shkruhet shqip (kartat përkthehen me kontrollin e numrave).
- **Bisedat** ruhen në Neo4j: `(:Person)-[:KA_BISEDE]->(:Bisede)-[:PERMBAN]->(:Mesazh)` (`bisedat.py`),
  bashkë me kartat dhe kontekstin, që biseda të vazhdojë kur rihapet. Vizitorët nuk ruajnë asgjë në databazë.
- Teksti i përgjigjeve shfaqet pa emoji (`web/pergjigja.py`); ndërfaqja ka ikona të pakta e të njëtrajtshme.
- Ikona dhe logot rikrijohen me `python assets/krijo_ikonen.py`.

## Instalimi nga GitHub

```
git clone <url-i-repos> chatbot_industri
cd chatbot_industri
python -m venv venv_chatbot
venv_chatbot\Scripts\pip install -r requirements.txt
copy .env.example .env           # plotëso fjalëkalimet
ollama pull bge-m3 && ollama pull gemma3:4b
python ngarko_grafin.py          # ngarkon bazën e njohurive në Neo4j
python -m web                    # http://localhost:8501
```

`neo4j_local/`, `data/burime/` (datasetet, rikrijohen me `shkarko_datasetet.py`) dhe `.env` nuk ngarkohen në GitHub.

## Si funksionon

```
mesazhi ──► 1. Kontroll urgjence (rregulla)  ──► "Telefono 127/112"
        ──► 2. bge-m3 embedding ──► Neo4j vector index (:Fraze) ──► (:Simptome)
        ──► 3. Grafi: (:Simptome)-[:TRAJTOHET_ME]->(:Barna)-[:KUNDERINDIKOHET_PER]->(:Gjendje)
               barnat e kundërindikuara për profilin hiqen në Cypher
        ──► 4. Përgjigje standarde nga databaza + kartat me doza
        ──► 5. Pyetje vijuese (doza, alternativa, këshilla, mjeku, info) → nga databaza
        ──► 6. Pyetje e lirë → LLM (Ollama) me kontekstin nga grafi (dozat me numra filtrohen)
```

### 🧠 Mendim i thellë dhe shqipja e folur

FarmaBot e kupton shqipen ashtu si shkruhet në chat: gegërisht, pa ë/ç, me "q" për "ç", me shkurtime.

1. **Fjalori** (`data/fjalori_shqip.json` + `gjuha.py`, ~540 fjalë dhe ~30 shprehje): *"po m dhem kryt e kom zjarrmi"* →
   *"po më dhemb koka e kam temperaturë"*, *"s'po muj me marr frym"* → urgjencë, *"kam sheqer"* → diabet, *"lukthi"* → stomaku.
   Urgjencat, profili, qëllimet dhe kërkimi kontrollojnë edhe mesazhin origjinal, edhe variantin standard.
2. **Fraza të reja** (`zgjero_njohurite_3.py`): 260 fraza në gegërisht/chat. Çdo frazë ruhet në graf edhe në shqip standard.
3. **Mendimi** (butoni *Mendo më thellë* te fusha e shkrimit): modeli `qwen3:8b` mendon (thinking)
   për mesazhin, e rishkruan në shqip standard dhe thotë cilat simptoma përmend. **Vendimin e merr baza**: formulimi i
   modelit shtohet si kërkim, por simptoma pranohet me të njëjtat rregulla (prag ngjashmërie, fjalë kyçe). Hapat shfaqen
   live dhe pastaj mbyllen si *"🧠 Mendoi për 48 sekonda"*. Zgjat ~30 s deri në 2 min në këtë kompjuter (CPU).
   Urgjencat, përshëndetjet dhe pyetjet vijuese nga databaza ("sa herë ta marr?") përgjigjen menjëherë.
   Modeli zgjidhet te `.env`: `OLLAMA_THINK_MODEL=qwen3:8b` (nëse mungon, përdoret `OLLAMA_LLM_MODEL`).

### 🌐 Shqip dhe anglisht

Pyet në shqip → përgjigje në shqip; pyet në anglisht → përgjigje në anglisht. Anglishtja kthehet në shqip me
`data/fjalori_anglisht.json`, kalon nga e njëjta logjikë (urgjenca, filtrimi, dozat), dhe përgjigjja përkthehet me
gemma3:4b, me fjalor termash (`data/terma_en.json`) dhe **kontroll numrash**: nëse një dozë/numër ndryshon, përkthimi
refuzohet. Urgjencat në anglisht kanë tekst fiks. Përkthimet ruhen te `data/perkthime_en.json`.

### 📚 Datasetet mjekësore

- **MedlinePlus** (NLM, SHBA): ~1 000 tema shëndetësore → 2 983 pjesë në Neo4j.
- **openFDA**: fletëudhëzuesit zyrtarë për 53 ilaçe të bazës → 575 pjesë, të lidhura me `(:Barna)`.
- Në mendimin e thellë, kodi kontrollon nëse fletëudhëzuesi zyrtar përmend gjendjet e profilit (shtatzëni, mëlçi,
  hollim gjaku...) dhe e thotë në shqip; teksti origjinal shfaqet te karta. Dozat mbeten **gjithmonë** nga baza.
- `python shkarko_datasetet.py` → `python ngarko_burimet.py` (~20 min embeddings në CPU).

### 📄 Dokumentimi

`dokumentimi/FarmaBot_Prezantimi.pptx` (15 slajde), `dokumentimi/FarmaBot_Dokumentimi.docx` dhe `.pdf` (34 faqe).
Rikrijohen me `dokumentimi/krijo_prezantimin.py` dhe `krijo_dokumentimin.py` (kërkojnë python-pptx / python-docx).

### Biseda që vazhdon (pa rinisje)

Bota mban mend temën: simptomat dhe barnat e fundit, dhe pyetjen sqaruese në pritje.

| Personi shkruan | FarmaBot |
|---|---|
| "përshëndetje", "faleminderit", "ok", "mirupafshim" | përgjigje e shkurtër, konteksti mbetet |
| "kam kollë" | pyet: *e thatë apo me gëlbazë?* → "e thatë" |
| "më dhemb" (e paqartë) | liston 2–3 mundësi → personi shkruan "2" |
| "kam **edhe** temperaturë" | shton simptomën te ato të mëparshmet |
| "sa herë ta marr?", "para apo pas ushqimit?" | dozat e barnave të sugjeruara |
| "ilaç tjetër?", "nuk më bëri efekt" | alternativat |
| "çfarë tjetër të bëj?" / "kur duhet mjeku?" / "çfarë është?" | këshilla / shenjat e alarmit / info |
| "jam shtatzënë" | rillogarit barnat për të njëjtën temë |
| diçka që nuk e njeh | e thotë sinqerisht, nuk e lidh me temën e vjetër |

Përgjigjet kanë disa formulime dhe nuk përsëriten njëra pas tjetrës; barnat, dozat dhe shenjat e alarmit
mbeten gjithmonë të njëjtat (vijnë nga databaza).

Siguria nuk i lihet LLM-së: urgjencat, filtrimi i barnave dhe dozat vijnë nga rregullat dhe nga databaza.

## Skedarët

| Skedari | Çfarë bën |
|---|---|
| `data/njohurite.json` | Baza e njohurive: 74 barna, 63 simptoma/sëmundje/nevoja të përditshme (me info, ~665 fraza, shenja alarmi, këshilla), 25 gjendje |
| `data/njohurite.para_zgjerimit.json` | Kopja e bazës para zgjerimit të parë (20 barna, 19 simptoma) |
| `data/njohurite.para_zgjerimit_2.json` | Kopja e bazës para zgjerimit të dytë (50 barna, 47 simptoma) |
| `zgjero_njohurite.py` | Zgjerimi 2: fraza të reja (edhe gegërisht/pa ë-ç), fjalë kyçe, barna dhe sëmundje të reja |
| `zgjero_njohurite_3.py` | Zgjerimi 3: 260 fraza në shqipen e folur (gegërisht, chat). Kopja e vjetër: `data/njohurite.para_zgjerimit_3.json` |
| `data/fjalori_shqip.json`, `gjuha.py` | Fjalori i shqipes së folur → shqip standard |
| `ngarko_grafin.py` | Ngarkon JSON-in në Neo4j dhe krijon embeddings |
| `ngarko_pdf.py` | Ngarkon fletëudhëzues PDF nga `data/pdf/` (opsionale) |
| `chatbot.py` | Logjika: urgjenca, kërkimi, filtrimi, përgjigja |
| `web/` | Ndërfaqja web: `server.py` (API), `admin.py`, `pergjigja.py`, `static/` (HTML/CSS/JS) |
| `bisedat.py` | Bisedat e ruajtura në Neo4j |
| `testo.py` | Provë e shpejtë nga terminali |
| `tests/` | Testet automatike (pytest), shiko më poshtë |
| `.env` | Kredencialet e Neo4j dhe modelet (mos e ndaj me askënd) |

## Databaza e personave (`perdoruesit.py`)

```
(:Person {id, emer, mosha, shenime})-[:KA_GJENDJE]->(:Gjendje)
(:Person)-[:DERGOI]->(:Mesazh {roli, tekst, ora})-[:PER_SIMPTOMEN]->(:Simptome)
                                                 -[:SUGJEROI]->(:Barna)
```

Profili ndryshohet te **Cilësimet → Profili shëndetësor** (mosha, gjendjet, alergjitë). Gjendjet që personi
i shkruan në bisedë (p.sh. "jam shtatzënë") i shtohen profilit automatikisht. Vizitorët nuk ruajnë asgjë.
Këto janë të dhëna shëndetësore: ruaji vetëm me pëlqim dhe fshiji kur kërkohet.

## Nisja

1. Sigurohu që Ollama është ndezur dhe ke modelet: `ollama pull bge-m3`, `ollama pull gemma3:4b` dhe `ollama pull qwen3:8b` (mendimi).
2. Kliko dy herë ikonën **FarmaBot** në Desktop: nis Ollama, Neo4j lokal dhe aplikacionin, dhe hap shfletuesin.
   Për ta ndalur: `Ndal FarmaBot` në dosjen e projektit. Log-et janë te `logs\`.
3. Shfletuesi hapet te http://localhost:8501

Kur ndryshon `data/njohurite.json`, ekzekuto përsëri `python ngarko_grafin.py`.

### Çfarë përmban baza (zgjerimi 2)

- **Fjalori i frazave:** çdo simptomë ka 8–20 mënyra si e thonë njerëzit, edhe gegërisht dhe pa ë/ç
  (*"më dhemb kryet"*, *"kam zjarrmi"*, *"më dhemb gurmazi/kurrizi"*, *"më shkon barku"*, *"kam bark të zënë"*,
  *"më ha lëkura"*, *"s'po më merr gjumi"*, *"jam i këputur"*, *"kam covid"*...).
- **Sëmundje/nevoja të reja:** vitamina dhe imuniteti, mungesë hekuri (→ mjeku), ngërçe këmbësh, dalja e dhëmbëve te foshnja,
  skuqje pelenash, zgjebe, dyll në vesh, këmbë të rënda/variçe, mbrojtje nga mushkonjat dhe rriqrat, lemza, djersitje,
  rënie flokësh, flluska nga këpucët, buzë të çara, sy me qelb (→ mjeku), planifikim shtatzënie (acid folik).
- **Barna të reja:** benzidaminë (Tantum Verde), acetilcisteinë (ACC), shurup urthi (Prospan), balsam mentoli (Vicks),
  vitaminë D, vitaminë C, zink, multivitaminë, hekur, acid folik, magnez, probiotik, supozitor glicerine, senna,
  pastë zinku (Sudocrem), permetrinë, heparinë xhel (Lioton), aloe vera, repelent, pika për dyllin e veshit,
  leukoplast hidrokoloid (Compeed), antidjersë me klorur alumini, minoksidil, vazelinë/balsam buzësh.
- Te dalja e dhëmbëve te foshnja nuk jepen kartat me doza: dozat për fëmijë varen nga pesha (pyet farmacistin).

## Shënime

- **Lidhja me Neo4j** (`NEO4J_TRANSPORT` te `.env`): të dyja mënyrat lidhen me të njëjtën databazë Aura.
  - `auto` (parazgjedhja): provon Bolt-in; nëse rrjeti e bllokon portin 7687, kalon vetë në HTTPS.
  - `bolt`: drajveri klasik `neo4j+s://`, porti 7687 (më i shpejtë).
  - `https`: Neo4j Query API, porti 443 (punon edhe në rrjete që bllokojnë 7687).
- **Aura Free** pauzohet pas disa ditësh pa përdorim; rinise te https://console.neo4j.io
- Të dhënat e barnave janë për të rritur dhe duhen kontrolluar nga një farmacist
  para përdorimit me njerëz të vërtetë.
- FarmaBot jep informacion, nuk zëvendëson mjekun ose farmacistin.

## Regjistrimi

Emri i përdoruesit pranon shkronjat **shqipe dhe angleze** (përfshirë **ç, ë**, të mëdha ose të vogla),
shifra dhe `_ . -` (3–30 karaktere). Nuk dallon shkronjat e mëdha nga të voglat ("Ëndrra" = "ëndrra"),
dhe "ë" e shkruar me diakritik të veçantë normalizohet. Emri/pseudonimi pranon shkronja shqipe/angleze,
hapësira, `' . -`.

## Testet

```
venv_chatbot\Scripts\python -m pytest              # ~580 teste, ~40 sekonda (pa LLM)
venv_chatbot\Scripts\python -m pytest -m llm       # testet me modelin gjuhësor (më të ngadalta)
```

| Skedari | Çfarë teston |
|---|---|
| `test_te_dhenat.py` | integriteti i JSON-it, referencat, kundërindikimet kritike |
| `test_urgjenca.py` | urgjencat dhe vetëdëmtimi kapen; simptomat e lehta jo |
| `test_profili.py` | gjendjet nga teksti, mohimi, mosha, qëllimet e bisedës |
| `test_regjistrimi.py` | shkronjat shqipe/angleze, hyrja, fjalëkalimi, fshirja |
| `test_simptomat.py` | ~150 mënyra si e shkruajnë njerëzit simptomën; mesazhe pa lidhje |
| `test_siguria.py` | çdo kundërindikim në databazë × çdo simptomë (gjenerohet nga të dhënat) |
| `test_biseda.py` | biseda me shumë mesazhe, sqarime, pyetje vijuese, larmia e përgjigjeve |
| `test_web.py` | aplikacioni web: hyrja, regjistrimi, bisedat, profili, gjuha, admini |
| `test_gjuha.py` | fjalori: gegërisht/chat → standard, urgjenca e profili në gegërisht, mendimi i thellë (`-m llm`) |

Testet që kanë nevojë për Neo4j/Ollama anashkalohen vetë nëse shërbimet nuk janë ndezur.
Llogaritë e testit krijohen me emër `test_...` dhe fshihen në fund.

## Rolet dhe panelet

| Roli | Çfarë sheh |
|---|---|
| **Vizitor** (pa llogari) | Biseda (asgjë nuk ruhet pasi mbyll faqen) |
| **Përdorues** | Biseda të ruajtura + Cilësimet (profili, fjalëkalimi, fshirja e llogarisë) |
| **Admin** | të gjitha + Paneli i administratorit: Përmbledhje · Përdoruesit · Ilaçet · Backup |

- Herën e parë krijohet automatikisht llogaria **admin**. Fjalëkalimi është te `.env` (`ADMIN_PASSWORD`). Ndryshoje pas hyrjes së parë te Cilësimet → Llogaria.
- Fjalëkalimet ruhen në Neo4j vetëm si hash PBKDF2-SHA256 me kripë: `(:Llogari)-[:ESHTE]->(:Person)`.
- Ndryshimet te 💊 Barnat ruhen në Neo4j dhe te `data/njohurite.json`.

## Neo4j Desktop dhe backup

- **💾 Backup** (paneli admin, ose `python backup.py`) ruan `Desktop\FarmaBot_Backup\<data_ora>\` me
  `databaza.json` dhe `databaza.cypher`. Ky skript e rikrijon databazën në çdo Neo4j.
- **Ta shohësh databazën Aura në Neo4j Desktop:** Neo4j Desktop → *Connect* → *Remote connection*.
  Përdor URI-në, përdoruesin dhe fjalëkalimin nga `.env`. Ke të njëjtat të dhëna, live.
- **Kopje lokale:** krijo një *Local instance* në Neo4j Desktop, nise dhe shto te `.env`
  `NEO4J_LOCAL_URI=neo4j://127.0.0.1:7687`, `NEO4J_LOCAL_USERNAME=neo4j`, `NEO4J_LOCAL_PASSWORD=...`.
  Pastaj përdor butonin "Kopjo Aura → Neo4j Desktop" (ose `python backup.py --lokal`).

## Databaza lokale (aktive)

Databaza kryesore tani është **Neo4j lokal** te `neo4j_local\` (Neo4j Community 2026.10.1 me Java 25 brenda dosjes),
vetëm në `127.0.0.1`. Të dhënat u kopjuan nga Aura më 2026-11-19. Kredencialet e Aura-s janë ruajtur
te `.env` si `NEO4J_AURA_*`.

- Neo4j Browser: http://localhost:7474 (përdoruesi `neo4j`, fjalëkalimi `NEO4J_PASSWORD` te `.env`)
- Neo4j Desktop: *Connect* → *Remote connection* → `bolt://127.0.0.1:7687`
- Aplikacioni dëgjon vetëm në `localhost` (të dhëna shëndetësore).
