"""Krijon dokumentimi/FarmaBot_Prezantimi.pptx (15 slajde, skema me forma native që redaktohen në PowerPoint).

Ekzekuto me një Python që ka python-pptx:   python dokumentimi/krijo_prezantimin.py
Numrat (ilaçe, simptoma, fraza, teste) lexohen nga projekti, që prezantimi të mbetet i saktë.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
DALJA = ROOT / "dokumentimi" / "FarmaBot_Prezantimi.pptx"

# ---------------------------------------------------------------- ngjyrat dhe shkronjat
TEAL = RGBColor(0x0E, 0x4D, 0x57)      # dominuese
TEAL2 = RGBColor(0x16, 0x6B, 0x77)
MINT = RGBColor(0x3F, 0xB8, 0xA0)      # dytësore
MINT_L = RGBColor(0xE6, 0xF5, 0xF1)    # sfond kartash
KORAL = RGBColor(0xF2, 0x6B, 0x4F)     # theks
KORAL_L = RGBColor(0xFD, 0xE9, 0xE4)
TEKST = RGBColor(0x1F, 0x2A, 0x30)
GRI = RGBColor(0x5B, 0x6B, 0x73)
GRI_L = RGBColor(0xF3, 0xF6, 0xF7)
BARDHE = RGBColor(0xFF, 0xFF, 0xFF)
KOKA, TRUPI = "Cambria", "Calibri"


# ---------------------------------------------------------------- numrat nga projekti
def numrat() -> dict:
    d = json.loads((ROOT / "data" / "njohurite.json").read_text(encoding="utf-8"))
    f = json.loads((ROOT / "data" / "fjalori_shqip.json").read_text(encoding="utf-8"))
    e = json.loads((ROOT / "data" / "fjalori_anglisht.json").read_text(encoding="utf-8"))
    n = {"barna": len(d["barnat"]), "simptoma": len(d["simptomat"]), "gjendje": len(d["gjendjet"]),
         "fraza": sum(len(s["fraza"]) for s in d["simptomat"]),
         "fjale": sum(len(v) for v in f["fjale"].values()),
         "shprehje": len(f["shprehje_para"]) + len(f["shprehje_pas"]), "shprehje_en": len(e["shprehje"])}
    py = ROOT / "venv_chatbot" / "Scripts" / "python.exe"
    dalja = subprocess.run([str(py), "-m", "pytest", "--co", "-q", "-p", "no:cacheprovider"], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    teste = {}
    for rresht in dalja.splitlines():
        # pytest.ini ka "-q", kështu që "--co -q" jep "tests/test_x.py: 12" (ose "...::emri" me më pak -q)
        m = re.match(r"^tests[/\\](test_\w+)\.py(?:: (\d+)$|::)", rresht.strip())
        if m:
            teste[m.group(1)] = teste.get(m.group(1), 0) + (int(m.group(2)) if m.group(2) else 1)
    n["teste"] = teste
    n["teste_gjithsej"] = sum(teste.values())
    return n


# ---------------------------------------------------------------- ndihmës
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BOSH = prs.slide_layouts[6]
SL = []


def _font(run, size, bold=False, color=TEKST, face=TRUPI, italic=False):
    run.font.size, run.font.bold, run.font.italic = Pt(size), bold, italic
    run.font.color.rgb, run.font.name = color, face


def tekst(sl, x, y, w, h, rreshta, size=16, color=TEKST, bold=False, face=TRUPI, align=PP_ALIGN.LEFT,
          anchor=MSO_ANCHOR.TOP, emri=None, hapesire=4):
    """rreshta: str ose listë; një element mund të jetë (tekst, {opsione})."""
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if emri:
        tb.name = emri
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, r in enumerate([rreshta] if isinstance(rreshta, str) else rreshta):
        t, o = (r, {}) if isinstance(r, str) else r
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = o.get("align", align)
        p.space_after = Pt(o.get("hapesire", hapesire))
        run = p.add_run()
        run.text = t
        _font(run, o.get("size", size), o.get("bold", bold), o.get("color", color), o.get("face", face),
              o.get("italic", False))
    return tb


def kuti(sl, x, y, w, h, fill=MINT_L, line=None, rrumbullak=True, emri=None, hije=False):
    sh = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rrumbullak else MSO_SHAPE.RECTANGLE,
                             Inches(x), Inches(y), Inches(w), Inches(h))
    if rrumbullak:
        sh.adjustments[0] = 0.12
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line:
        sh.line.color.rgb, sh.line.width = line, Pt(1.25)
    else:
        sh.line.fill.background()
    if not hije:
        sp = sh._element.spPr
        sp.append(sp.makeelement(qn("a:effectLst"), {}))
    if emri:
        sh.name = emri
    sh.text_frame.margin_left = sh.text_frame.margin_right = Inches(0.12)
    return sh


def kuti_me_tekst(sl, x, y, w, h, titull, nen=None, fill=MINT_L, ngjyra=TEAL, size=15, nen_size=12, emri=None,
                  line=None):
    sh = kuti(sl, x, y, w, h, fill=fill, line=line, emri=emri)
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = titull
    _font(r, size, True, ngjyra)
    if nen:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = nen
        _font(r2, nen_size, False, GRI if fill not in (TEAL, TEAL2, KORAL) else BARDHE)
    return sh


def rreth(sl, x, y, d, simbol, fill=TEAL, ngjyra=BARDHE, size=20, emri=None):
    sh = sl.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    tf = sh.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = simbol
    _font(r, size, True, ngjyra, face="Segoe UI Emoji" if not simbol.isalnum() else TRUPI)
    if emri:
        sh.name = emri
    return sh


def shigjete(sl, x1, y1, x2, y2, ngjyra=GRI, etiketa=None, size=11, dx=0.0, dy=-0.28):
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb, c.line.width = ngjyra, Pt(1.75)
    ln = c.line._get_or_add_ln()
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    if etiketa:
        mx, my = (x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy
        tekst(sl, mx - 1.3, my, 2.6, 0.3, etiketa, size=size, color=ngjyra, bold=True, align=PP_ALIGN.CENTER)
    return c


def slajd(titull, nentitull=None, sfond=BARDHE, shenime=""):
    sl = prs.slides.add_slide(BOSH)
    sl.background.fill.solid()
    sl.background.fill.fore_color.rgb = sfond
    if titull:
        tekst(sl, 0.6, 0.45, 12.1, 0.7, titull, size=34, bold=True, face=KOKA,
              color=BARDHE if sfond == TEAL else TEAL, emri="Titulli")
    if nentitull:
        tekst(sl, 0.6, 1.15, 12.1, 0.45, nentitull, size=16, color=GRI if sfond != TEAL else MINT_L,
              emri="Nentitulli")
    nr = len(prs.slides)
    if nr > 1:
        tekst(sl, 12.2, 7.0, 0.6, 0.3, str(nr), size=10, color=GRI if sfond != TEAL else MINT_L,
              align=PP_ALIGN.RIGHT, emri="Numri")
        tekst(sl, 0.6, 7.0, 4, 0.3, "FarmaBot", size=10, color=GRI if sfond != TEAL else MINT_L, emri="Fundi")
    if shenime:
        sl.notes_slide.notes_text_frame.text = shenime
    return sl


N = numrat()


def ndaj_mijeshet(x: int) -> str:
    return f"{x:,}".replace(",", " ")


# ================================================================ 1. Titulli
sl = slajd(None, sfond=TEAL, shenime="FarmaBot: asistent informues farmacie që kupton shqipen e folur dhe anglishten.")
rreth(sl, 0.9, 1.6, 1.3, "💊", fill=MINT, size=40)
tekst(sl, 0.9, 3.1, 11, 1.1, "FarmaBot", size=60, bold=True, face=KOKA, color=BARDHE, emri="Titulli")
tekst(sl, 0.9, 4.25, 11, 0.6, "Asistent farmacie në shqip · GraphRAG lokal me Neo4j dhe Ollama",
      size=22, color=MINT_L, emri="Nentitulli")
tekst(sl, 0.9, 5.2, 11, 0.5, "Simptoma → ilaçe pa recetë të sigurta për profilin → kur duhet mjeku",
      size=16, color=BARDHE)
tekst(sl, 0.9, 6.6, 6, 0.4, "Prezantimi teknik · 2026", size=12, color=MINT_L)

# ================================================================ 2. Çfarë është
sl = slajd("Çfarë është FarmaBot", "Një bisedë e thjeshtë, me sigurinë e një databaze",
           shenime="Personi shkruan si flet. Bota i kupton simptomat, heq ilaçet e pasigurta dhe tregon kur duhet mjeku.")
rreshtat = [("💬", "Shkruan si flet", "Shqip standard, gegërisht, pa ë/ç, ose anglisht"),
            ("💊", "Merr ilaçe pa recetë", "Vetëm ato që janë të sigurta për moshën dhe gjendjet e tij"),
            ("🩺", "Mëson kur duhet mjeku", "Shenjat e alarmit dhe urgjencat 127 / 112, menjëherë")]
for i, (ik, t, n) in enumerate(rreshtat):
    y = 1.95 + i * 1.5
    rreth(sl, 0.7, y, 0.9, ik, fill=MINT, size=24)
    tekst(sl, 1.85, y + 0.05, 5.0, 0.4, t, size=20, bold=True, color=TEAL)
    tekst(sl, 1.85, y + 0.5, 5.0, 0.5, n, size=15, color=GRI)
statet = [(N["barna"], "ilaçe pa recetë"), (N["simptoma"], "simptoma dhe nevoja"),
          (N["fraza"], "fraza si flasin njerëzit"), (3558, "pjesë nga burime zyrtare")]
for i, (v, e) in enumerate(statet):
    x, y = 7.3 + (i % 2) * 2.85, 1.95 + (i // 2) * 2.3
    kuti(sl, x, y, 2.6, 2.0, fill=MINT_L if i < 3 else KORAL_L)
    tekst(sl, x, y + 0.3, 2.6, 0.9, ndaj_mijeshet(v), size=44, bold=True, face=KOKA,
          color=TEAL if i < 3 else KORAL, align=PP_ALIGN.CENTER)
    tekst(sl, x + 0.15, y + 1.25, 2.3, 0.6, e, size=14, color=GRI, align=PP_ALIGN.CENTER)

# ================================================================ 3. Arkitektura
sl = slajd("Arkitektura", "Gjithçka punon lokalisht në kompjuter: asnjë e dhënë shëndetësore nuk del jashtë",
           shenime="Streamlit tregon bisedën; chatbot.py merr vendimet; Neo4j ruan grafin dhe vektorët; Ollama jep modelet.")
kuti_me_tekst(sl, 0.6, 3.05, 1.9, 1.3, "👤 Personi", "shfletuesi\nlocalhost:8501", fill=GRI_L)
kuti_me_tekst(sl, 3.1, 3.05, 2.3, 1.3, "Streamlit", "app.py · faqet/", fill=MINT_L)
kuti_me_tekst(sl, 6.0, 2.75, 2.6, 1.9, "chatbot.py", "urgjenca · kërkimi\nfiltrimi · përgjigja", fill=TEAL,
              ngjyra=BARDHE, size=18)
kuti_me_tekst(sl, 6.0, 5.35, 2.6, 1.15, "gjuha.py · perkthimi.py", "shqip i folur · anglisht", fill=KORAL_L,
              ngjyra=KORAL, size=13)
kuti_me_tekst(sl, 9.6, 1.75, 3.1, 1.6, "Neo4j", "graf: ilaçe, simptoma, gjendje\nvektorë: fraza + burime\nbolt://127.0.0.1:7687",
              fill=MINT_L, size=17)
kuti_me_tekst(sl, 9.6, 4.15, 3.1, 1.6, "Ollama", "bge-m3 (embeddings)\nqwen3:8b (mendimi)\ngemma3:4b (përkthimi)",
              fill=MINT_L, size=17)
kuti_me_tekst(sl, 9.6, 6.05, 3.1, 0.75, "data/*.json → ngarko_grafin.py", fill=GRI_L, ngjyra=GRI, size=12)
shigjete(sl, 2.5, 3.7, 3.1, 3.7)
shigjete(sl, 5.4, 3.7, 6.0, 3.7)
shigjete(sl, 8.6, 3.2, 9.6, 2.6, etiketa="Cypher", dy=-0.4)
shigjete(sl, 8.6, 4.2, 9.6, 4.95, etiketa="HTTP", dy=0.12)
shigjete(sl, 7.3, 4.65, 7.3, 5.35)
shigjete(sl, 11.15, 6.05, 11.15, 5.75)

# ================================================================ 4. Lidhja me Neo4j
sl = slajd("Lidhja me Neo4j", "Një funksion i vetëm, query(), fsheh mënyrën e lidhjes nga i gjithë kodi",
           shenime="config.py lexon .env. NEO4J_TRANSPORT zgjedh bolt, https ose auto. Sot databaza aktive është lokale.")
kuti_me_tekst(sl, 0.6, 2.05, 2.7, 1.9, ".env", "NEO4J_URI\nNEO4J_USERNAME\nNEO4J_PASSWORD\nNEO4J_TRANSPORT", fill=GRI_L,
              ngjyra=TEAL, size=18)
kuti_me_tekst(sl, 3.9, 2.05, 2.7, 1.9, "config.py", "load_dotenv()\nmenyra_lidhjes()\nquery(cypher, **params)",
              fill=TEAL, ngjyra=BARDHE, size=18)
shigjete(sl, 3.3, 3.0, 3.9, 3.0)
for i, (t, n) in enumerate([("bolt", "drajveri neo4j · porti 7687\nmë i shpejti"),
                            ("https", "Query API · porti 443\npunon kur 7687 bllokohet"),
                            ("auto", "provon bolt për 10 s\npastaj kalon në https")]):
    y = 1.75 + i * 0.85
    kuti_me_tekst(sl, 7.4, y, 2.4, 0.72, t, fill=MINT_L, size=15)
    tekst(sl, 9.95, y + 0.05, 3.0, 0.7, n, size=12, color=GRI)
    shigjete(sl, 6.6, 3.0, 7.4, y + 0.36)
for i, (t, n, f) in enumerate([("Neo4j lokal (aktive)", "neo4j_local\\ · 127.0.0.1:7687\nvetëm në këtë kompjuter", MINT_L),
                               ("Neo4j Aura (cloud)", "NEO4J_AURA_* te .env\nkopja e mëparshme", GRI_L),
                               ("Backup", "backup.py → Desktop\\FarmaBot_Backup\ndatabaza.json + .cypher", KORAL_L)]):
    x = 0.6 + i * 4.15
    kuti(sl, x, 4.75, 3.85, 1.75, fill=f)
    tekst(sl, x + 0.3, 4.95, 3.3, 0.45, t, size=17, bold=True, color=KORAL if i == 2 else TEAL)
    tekst(sl, x + 0.3, 5.45, 3.3, 0.9, n, size=13, color=GRI)

# ================================================================ 5. Struktura e grafit
sl = slajd("Struktura e grafit", "Nyje dhe lidhje: filtrimi i ilaçeve bëhet drejt në Cypher",
           shenime="Simptoma lidhet me ilaçet me rend. Ilaçi lidhet me gjendjet ku nuk lejohet ose kërkon kujdes.")
D1, D2 = 1.75, 1.35  # diametrat: njohuritë (lart), përdoruesit/burimet (poshtë)
lart = {"Fraze": (0.7, GRI_L, TEAL), "Simptome": (3.7, MINT, BARDHE), "Barna\n(ilaçi)": (7.3, TEAL, BARDHE),
        "Gjendje": (10.6, KORAL, BARDHE)}
for emer, (x, f, c) in lart.items():
    rreth(sl, x, 1.85, D1, emer, fill=f, ngjyra=c, size=15, emri=f"Nyja {emer.split()[0]}")
YL, YP = 1.85 + D1 / 2, 4.75 + D2 / 2          # qendrat vertikale
poshte = {"Mesazh": 3.7 + (D1 - D2) / 2, "Chunk": 7.3 + (D1 - D2) / 2, "Person": 10.6 + (D1 - D2) / 2}
for emer, x in poshte.items():
    rreth(sl, x, 4.75, D2, emer, fill=MINT_L if emer != "Chunk" else GRI_L, ngjyra=TEAL, size=14, emri=f"Nyja {emer}")
shigjete(sl, 0.7 + D1, YL, 3.7, YL, etiketa="I_PERKET", ngjyra=TEAL2)
shigjete(sl, 3.7 + D1, YL, 7.3, YL, etiketa="TRAJTOHET_ME {rendi}", ngjyra=TEAL2)
shigjete(sl, 7.3 + D1, YL - 0.25, 10.6, YL - 0.25, etiketa="KUNDERINDIKOHET_PER", ngjyra=KORAL)
shigjete(sl, 7.3 + D1, YL + 0.25, 10.6, YL + 0.25, etiketa="KUJDES_ME", ngjyra=KORAL, dy=0.05)
qx = {k: v + D2 / 2 for k, v in poshte.items()}
shigjete(sl, qx["Mesazh"], 4.75, qx["Mesazh"], 1.85 + D1, etiketa="PER_SIMPTOMEN", ngjyra=GRI, dx=-1.05, dy=-0.15)
shigjete(sl, qx["Chunk"], 4.75, qx["Chunk"], 1.85 + D1, etiketa="PERSHKRUAN", ngjyra=TEAL2, dx=0.95, dy=-0.15)
shigjete(sl, qx["Person"], 4.75, qx["Person"], 1.85 + D1, etiketa="KA_GJENDJE", ngjyra=TEAL2, dx=0.95, dy=-0.15)
shigjete(sl, qx["Mesazh"] + 0.5, 4.85, 7.3 + 0.35, 1.85 + D1 - 0.25, etiketa="SUGJEROI", ngjyra=GRI, dx=0.75, dy=0.2)
# DERGOI: Person → Mesazh, si kënd poshtë rrathëve
yk = 4.75 + D2 + 0.28
for (x1, y1, x2, y2) in [(qx["Person"], 4.75 + D2, qx["Person"], yk), (qx["Person"], yk, qx["Mesazh"], yk)]:
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb, c.line.width = TEAL2, Pt(1.75)
shigjete(sl, qx["Mesazh"], yk, qx["Mesazh"], 4.75 + D2, ngjyra=TEAL2)
tekst(sl, (qx["Mesazh"] + qx["Person"]) / 2 - 1.5, yk + 0.05, 3.0, 0.3, "DERGOI (Person → Mesazh)", size=11,
      color=TEAL2, bold=True, align=PP_ALIGN.CENTER)
kuti(sl, 0.6, 4.75, 2.55, 1.35, fill=GRI_L)
tekst(sl, 0.75, 4.85, 2.3, 1.2, [("Llogaritë", {"size": 13, "bold": True, "color": TEAL}),
                                 ("(:Llogari)-[:ESHTE]->(:Person)", {"size": 11, "color": GRI}),
                                 ("Chunk = pjesë nga MedlinePlus, openFDA, PDF", {"size": 11, "color": GRI})])

# ================================================================ 6. Rrjedha e një mesazhi
sl = slajd("Rrjedha e një mesazhi", "Rregullat para modelit: urgjenca dhe siguria nuk varen kurrë nga modeli gjuhësor",
           shenime="Çdo mesazh kalon këto hapa me radhë. Urgjenca ndalon menjëherë rrjedhën.")
hapat = [("1", "Urgjenca", "rregulla → 127 / 112", KORAL), ("2", "Gjuha", "shqip i folur / anglisht", TEAL),
         ("3", "Profili", "“jam shtatzënë”, “5 vjeç”", TEAL), ("4", "Bisedë?", "përshëndetje, faleminderit", TEAL),
         ("5", "Simptoma", "bge-m3 + fjalë kyçe", TEAL), ("6", "Mendimi", "qwen3:8b kupton, baza vendos", MINT),
         ("7", "Ilaçet", "filtrim në Cypher", TEAL), ("8", "Përgjigja", "nga databaza + kartat", TEAL)]
for i, (nr, t, n, f) in enumerate(hapat):
    x, y = 0.6 + (i % 4) * 3.1, 2.0 + (i // 4) * 2.45
    kuti(sl, x, y, 2.8, 1.95, fill=GRI_L)
    rreth(sl, x + 0.25, y + 0.25, 0.65, nr, fill=f, size=18)
    tekst(sl, x + 1.05, y + 0.32, 1.7, 0.5, t, size=18, bold=True, color=TEAL)
    tekst(sl, x + 0.25, y + 1.1, 2.4, 0.7, n, size=13, color=GRI)
    if i % 4 != 3:
        shigjete(sl, x + 2.8, y + 0.98, x + 3.1, y + 0.98, ngjyra=MINT)

# ================================================================ 7. Fjalori shqip
sl = slajd("Fjalori i shqipes së folur", "Bota e kupton mesazhin ashtu si e shkruajnë njerëzit në chat",
           shenime="gjuha.standardizo() kthen variantin standard; kërkimi përdor edhe origjinalin, edhe variantin.")
shembuj = [("po m dhem kryt", "më dhemb koka"), ("kom zjarrmi qe dje", "kam temperaturë prej dje"),
           ("m djeg lukthi", "më djeg stomaku"), ("s'po muj me marr frym", "nuk mund të marr frymë  🚨"),
           ("kam sheqer", "kam diabet  (gjendje e profilit)")]
for i, (a, b) in enumerate(shembuj):
    y = 1.95 + i * 0.95
    kuti_me_tekst(sl, 0.6, y, 3.3, 0.72, a, fill=KORAL_L, ngjyra=KORAL, size=15)
    shigjete(sl, 3.95, y + 0.36, 4.55, y + 0.36, ngjyra=GRI)
    kuti_me_tekst(sl, 4.6, y, 3.9, 0.72, b, fill=MINT_L, ngjyra=TEAL, size=15)
for i, (v, e) in enumerate([(N["fjale"], "fjalë: gegërisht, chat, gabime"),
                            (N["shprehje"], "shprehje (m', s', “me + folje”)"),
                            (262, "fraza të reja në bazë")]):
    y = 1.95 + i * 1.6
    tekst(sl, 9.2, y, 3.6, 0.8, ndaj_mijeshet(v), size=42, bold=True, face=KOKA, color=TEAL)
    tekst(sl, 9.2, y + 0.85, 3.6, 0.5, e, size=14, color=GRI)

# ================================================================ 8. Shqip dhe anglisht
sl = slajd("Shqip dhe anglisht", "Pyet në shqip → përgjigje në shqip · pyet në anglisht → përgjigje në anglisht",
           shenime="Logjika mbetet në shqip. Anglishtja kthehet në shqip me fjalor; përgjigjja përkthehet me kontroll numrash.")
rrjedha = [("“I have a sore\nthroat since\nyesterday”", GRI_L, TEAL), ("Zbulimi i gjuhës\ngjuha_e_mesazhit()", MINT_L, TEAL),
           ("Fjalor EN → SQ\n“kam dhimbje fyti\nprej dje”", MINT_L, TEAL), ("E njëjta logjikë\nurgjenca · baza\nfiltrimi", TEAL, BARDHE),
           ("Përkthim në EN\nfjalor termash +\nkontroll numrash", KORAL_L, KORAL)]
for i, (t, f, c) in enumerate(rrjedha):
    x = 0.6 + i * 2.5
    kuti_me_tekst(sl, x, 2.35, 2.15, 1.85, t, fill=f, ngjyra=c, size=14)
    if i < 4:
        shigjete(sl, x + 2.15, 3.27, x + 2.5, 3.27, ngjyra=MINT)
for i, (ik, t) in enumerate([("🚨", "Urgjencat në anglisht kanë tekst fiks: pa model, menjëherë"),
                             ("🔢", "Nëse një numër (dozë, orë) ndryshon gjatë përkthimit, përkthimi refuzohet"),
                             ("📘", f"{N['shprehje_en']} shprehje angleze dhe fjalor termash mjekësorë i shkruar me dorë")]):
    y = 4.75 + i * 0.7
    rreth(sl, 0.6, y, 0.5, ik, fill=MINT, size=13)
    tekst(sl, 1.3, y + 0.08, 11, 0.45, t, size=15, color=TEKST)

# ================================================================ 9. Mendimi i thellë
sl = slajd("Mendimi i thellë", "Si te Claude: bota mendon disa sekonda deri në 1–2 minuta dhe të tregon çfarë po bën",
           shenime="Modeli e lexon mesazhin; vendimi mbetet te baza. Urgjencat dhe pyetjet vijuese nuk presin.")
afati = [("📖", "Lexon mesazhin", "fjalori: “kryt” → “koka”"), ("🧠", "Mendon (qwen3:8b)", "e rishkruan në shqip standard"),
         ("🔎", "Krahason me bazën", "pranon vetëm me pragun dhe fjalët kyçe"),
         ("💊", "Kontrollon ilaçet", "kundërindikimet për profilin"),
         ("📚", "Lexon fletëudhëzuesit", "openFDA: a përmendet gjendja jote?"),
         ("✅", "Përgjigjet", "“🧠 Mendoi për 48 sekonda”")]
for i, (ik, t, n) in enumerate(afati):
    y = 1.85 + i * 0.85
    rreth(sl, 0.7, y, 0.62, ik, fill=TEAL if i not in (1, 5) else MINT, size=15)
    if i < 5:
        shigjete(sl, 1.01, y + 0.62, 1.01, y + 0.85, ngjyra=MINT)
    tekst(sl, 1.6, y + 0.02, 3.6, 0.4, t, size=17, bold=True, color=TEAL)
    tekst(sl, 4.7, y + 0.06, 4.0, 0.4, n, size=14, color=GRI)
kuti(sl, 9.0, 1.95, 3.75, 2.4, fill=TEAL)
tekst(sl, 9.3, 2.2, 3.2, 1.2, "“Modeli kupton,\nbaza vendos.”", size=26, bold=True, face=KOKA, color=BARDHE)
tekst(sl, 9.3, 3.45, 3.2, 0.8, "Formulimi i modelit është vetëm një kërkim më shumë.", size=13, color=MINT_L)
kuti(sl, 9.0, 4.6, 3.75, 1.9, fill=KORAL_L)
tekst(sl, 9.3, 4.8, 3.2, 0.4, "Pa pritje", size=17, bold=True, color=KORAL)
tekst(sl, 9.3, 5.25, 3.2, 1.2, "Urgjencat, përshëndetjet dhe “sa herë ta marr?” përgjigjen menjëherë.",
      size=13, color=TEKST)

# ================================================================ 10. Datasetet
sl = slajd("Datasetet mjekësore", "Burime publike dhe zyrtare, të ngarkuara në Neo4j si vektorë (bge-m3)",
           shenime="MedlinePlus dhe openFDA janë në anglisht; bge-m3 i gjen edhe me pyetje shqip. Dozat mbeten nga baza.")
for i, (emer, v, e, pershkrim, f, c) in enumerate([
        ("MedlinePlus", 2983, "pjesë teksti", "~1 000 tema shëndetësore të Bibliotekës Kombëtare të Mjekësisë (SHBA)", MINT_L, TEAL),
        ("openFDA", 575, "pjesë teksti", "fletëudhëzuesit zyrtarë për 53 nga ilaçet e bazës", KORAL_L, KORAL),
        ("Baza FarmaBot", N["fraza"], "fraza", f"{N['barna']} ilaçe · {N['simptoma']} simptoma · {N['gjendje']} gjendje", GRI_L, TEAL)]):
    x = 0.6 + i * 4.15
    kuti(sl, x, 1.95, 3.85, 3.2, fill=f)
    tekst(sl, x + 0.3, 2.15, 3.3, 0.5, emer, size=20, bold=True, color=c)
    tekst(sl, x + 0.3, 2.7, 3.3, 0.9, ndaj_mijeshet(v), size=46, bold=True, face=KOKA, color=c)
    tekst(sl, x + 0.3, 3.6, 3.3, 0.4, e, size=14, color=GRI)
    tekst(sl, x + 0.3, 4.05, 3.3, 1.0, pershkrim, size=13, color=TEKST)
tekst(sl, 0.6, 5.55, 12.1, 0.9, [
    ("Si përdoren: kodi kontrollon nëse fletëudhëzuesi zyrtar përmend gjendjet e profilit (shtatzëni, mëlçi, "
     "ilaçe për hollimin e gjakut...) dhe e thotë në shqip; teksti origjinal tregohet te karta.", {"size": 15}),
    ("Shkarkimi: shkarko_datasetet.py · ngarkimi: ngarko_burimet.py", {"size": 13, "color": GRI})])

# ================================================================ 11. Siguria
sl = slajd("Siguria", "Çdo vendim i rrezikshëm merret nga rregullat dhe databaza, jo nga modeli",
           shenime="Gjashtë mbrojtje të pavarura. Modeli gjuhësor nuk zgjedh dot ilaç dhe nuk shkruan dot doza.")
mbrojtjet = [("🚨", "Urgjencat me rregulla", "regex para çdo modeli; 127 / 112"),
             ("⛔", "Filtrim në Cypher", "ilaçet e kundërindikuara hiqen para modelit"),
             ("💊", "Dozat nga databaza", "kartat lexojnë JSON-in, jo tekstin e modelit"),
             ("✂️", "pastro_dozat()", "rreshtat me doza numerike te teksti i modelit hiqen"),
             ("🔢", "Kontroll numrash", "përkthimi refuzohet nëse ndryshon një numër"),
             ("🔒", "Të dhënat lokale", "Neo4j në 127.0.0.1 · fjalëkalime PBKDF2")]
for i, (ik, t, n) in enumerate(mbrojtjet):
    x, y = 0.6 + (i % 3) * 4.15, 1.95 + (i // 3) * 2.45
    kuti(sl, x, y, 3.85, 2.15, fill=GRI_L)
    rreth(sl, x + 0.3, y + 0.3, 0.75, ik, fill=KORAL if i == 0 else TEAL, size=18)
    tekst(sl, x + 1.25, y + 0.42, 2.5, 0.5, t, size=17, bold=True, color=TEAL)
    tekst(sl, x + 0.3, y + 1.25, 3.3, 0.8, n, size=14, color=GRI)

# ================================================================ 12. Llogaritë dhe rolet
sl = slajd("Llogaritë dhe rolet", "Tre nivele, nga biseda anonime te paneli i administrimit",
           shenime="Vizitori nuk ruan asgjë. Përdoruesi ruan profilin me pëlqim. Admini menaxhon ilaçet dhe backup-in.")
rolet = [("👋", "Vizitor", "pa llogari", ["💬 Biseda", "Asgjë nuk ruhet"], GRI_L),
         ("👤", "Përdorues", "me pëlqim", ["💬 Biseda", "👤 Llogaria ime", "Profili dhe historia", "Fshi të dhënat e mia"], MINT_L),
         ("🛡️", "Admin", "ADMIN_PASSWORD te .env", ["Gjithçka e përdoruesit", "📊 Përmbledhje", "👥 Përdoruesit",
                                                   "💊 Ilaçet", "💾 Backup"], TEAL)]
for i, (ik, t, n, lista, f) in enumerate(rolet):
    x = 0.6 + i * 4.15
    kuti(sl, x, 1.95, 3.85, 4.4, fill=f)
    c = BARDHE if f == TEAL else TEAL
    rreth(sl, x + 0.3, 2.2, 0.8, ik, fill=MINT if f == TEAL else TEAL, size=20)
    tekst(sl, x + 1.3, 2.25, 2.4, 0.45, t, size=22, bold=True, color=c)
    tekst(sl, x + 1.3, 2.72, 2.4, 0.4, n, size=12, color=MINT_L if f == TEAL else GRI)
    tekst(sl, x + 0.35, 3.45, 3.2, 2.8, [(z, {"size": 15, "color": c, "hapesire": 8}) for z in lista])
tekst(sl, 0.6, 6.5, 12.1, 0.4, "Fjalëkalimet: hash PBKDF2-SHA256 me kripë, në (:Llogari)-[:ESHTE]->(:Person)",
      size=13, color=GRI)

# ================================================================ 13. Testet
sl = slajd("Testet", f"{N['teste_gjithsej']} teste automatike me pytest; testet me modelin ndahen me  -m llm",
           shenime="Testet që kanë nevojë për Neo4j/Ollama anashkalohen vetë kur shërbimet nuk janë ndezur.")
emrat_e_bukur = {"test_siguria": "siguria", "test_simptomat": "simptomat", "test_gjuha": "gjuha", "test_biseda": "biseda",
                 "test_profili": "profili", "test_urgjenca": "urgjenca", "test_te_dhenat": "të dhënat",
                 "test_regjistrimi": "regjistrimi", "test_nderfaqja": "ndërfaqja", "test_anglisht": "anglisht"}
renditja = sorted(N["teste"].items(), key=lambda kv: kv[1])
cd = CategoryChartData()
cd.categories = [emrat_e_bukur.get(k, k) for k, _ in renditja]
cd.add_series("Teste", [v for _, v in renditja])
gf = sl.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.8), Inches(8.2), Inches(5.0), cd)
ch = gf.chart
ch.has_legend = False
ch.has_title = False
ch.plots[0].gap_width = 60
ch.plots[0].has_data_labels = True
dl = ch.plots[0].data_labels
dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size, dl.font.color.rgb, dl.font.name = Pt(12), TEKST, TRUPI
ser = ch.series[0]
ser.format.fill.solid()
ser.format.fill.fore_color.rgb = TEAL
ch.category_axis.tick_labels.font.size = Pt(13)
ch.category_axis.tick_labels.font.color.rgb = GRI
ch.category_axis.format.line.fill.background()
ch.value_axis.visible = False
ch.value_axis.has_major_gridlines = False
kuti(sl, 9.3, 1.95, 3.45, 2.2, fill=TEAL)
tekst(sl, 9.3, 2.15, 3.45, 1.0, ndaj_mijeshet(N["teste_gjithsej"]), size=54, bold=True, face=KOKA, color=BARDHE,
      align=PP_ALIGN.CENTER)
tekst(sl, 9.5, 3.25, 3.05, 0.7, "teste automatike", size=16, color=MINT_L, align=PP_ALIGN.CENTER)
tekst(sl, 9.3, 4.5, 3.45, 2.0, [("python -m pytest", {"size": 14, "face": "Consolas", "color": TEAL}),
                                ("python -m pytest -m llm", {"size": 14, "face": "Consolas", "color": TEAL}),
                                ("(i dyti: testet me modelin)", {"size": 12, "color": GRI}),
                                ("Më të shumtat: çdo kundërindikim × çdo simptomë", {"size": 13, "color": GRI})])

# ================================================================ 14. Nisja e sistemit
sl = slajd("Nisja e sistemit", "Një klik te ikona FarmaBot në Desktop, ose nis_farmabot.ps1",
           shenime="Skripti nis me radhë Ollama, Neo4j lokal dhe Streamlit, dhe pret që secili porti të hapet.")
for i, (nr, t, n, porti) in enumerate([("1", "Ollama", "bge-m3 · qwen3:8b · gemma3:4b", "11434"),
                                       ("2", "Neo4j lokal", "neo4j_local\\ me Java brenda", "7687 · 7474"),
                                       ("3", "FarmaBot", "streamlit run app.py", "8501")]):
    x = 0.6 + i * 4.15
    kuti(sl, x, 2.0, 3.85, 2.6, fill=MINT_L)
    rreth(sl, x + 0.3, 2.25, 0.8, nr, fill=TEAL, size=22)
    tekst(sl, x + 1.3, 2.38, 2.4, 0.5, t, size=22, bold=True, color=TEAL)
    tekst(sl, x + 0.3, 3.3, 3.3, 0.5, n, size=14, color=GRI)
    tekst(sl, x + 0.3, 3.85, 3.3, 0.5, f"porti {porti}", size=15, bold=True, color=KORAL)
    if i < 2:
        shigjete(sl, x + 3.85, 3.3, x + 4.15, 3.3, ngjyra=MINT)
tekst(sl, 0.6, 5.05, 12.1, 1.6, [
    ("Herën e parë:  ollama pull bge-m3 · qwen3:8b · gemma3:4b", {"size": 15}),
    ("Pas ndryshimit të njohurive:  python ngarko_grafin.py   ·   burimet:  python shkarko_datasetet.py  →  ngarko_burimet.py",
     {"size": 15}),
    ("Ndalimi: “Ndal FarmaBot” · log-et te logs\\ · shfletuesi: http://localhost:8501", {"size": 15, "color": GRI})])

# ================================================================ 15. Përmbyllje
sl = slajd(None, sfond=TEAL, shenime="Përmbledhje dhe pyetje.")
tekst(sl, 0.9, 1.3, 11, 0.9, "Përmbledhje", size=44, bold=True, face=KOKA, color=BARDHE, emri="Titulli")
for i, t in enumerate(["Kupton shqipen e folur dhe anglishten",
                       "Mendon para se të përgjigjet, dhe tregon hapat",
                       "Siguria: rregulla dhe databazë, jo hamendësime",
                       "Burime zyrtare: MedlinePlus dhe openFDA"]):
    y = 2.45 + i * 0.78
    rreth(sl, 0.9, y, 0.5, "✓", fill=MINT, size=16)
    tekst(sl, 1.65, y + 0.06, 10, 0.5, t, size=20, color=BARDHE)
tekst(sl, 0.9, 5.85, 11, 0.6, "Pyetje?", size=28, bold=True, face=KOKA, color=MINT_L)
tekst(sl, 0.9, 6.45, 11.5, 0.4, "FarmaBot jep informacion; nuk zëvendëson farmacistin ose mjekun.", size=12, color=MINT_L)

prs.core_properties.title = "FarmaBot: prezantimi teknik"
prs.core_properties.author = "FarmaBot"
DALJA.parent.mkdir(parents=True, exist_ok=True)
prs.save(DALJA)
print(f"U ruajt: {DALJA} ({len(prs.slides)} slajde, {N['teste_gjithsej']} teste)")
