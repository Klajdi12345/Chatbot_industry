"""Krijon dokumentimi/FarmaBot_Databaza.docx: gjithçka për databazën Neo4j të FarmaBot-it.

Ku ndodhet databaza në disk, si lidhesh, çfarë nyjesh dhe lidhjesh ka, ku ruhen përdoruesit, fjalëkalimet,
bisedat, reagimet dhe backup-et, si bëhet dhe si rikthehet një backup. Numrat, kufizimet, indekset dhe lista e
backup-eve lexohen drejt nga databaza dhe disku kur ekzekutohet skripti, që dokumenti të jetë gjithmonë i saktë.

    python dokumentimi/krijo_databazen.py      (Neo4j duhet të jetë ndezur)

Fjalëkalimet NUK shkruhen në dokument: tregohet vetëm ku ndodhen (.env), që dokumenti të ndahet pa rrezik.
PDF-ja krijohet pastaj me Word, njësoj si dokumentimi kryesor.
"""
import os
import re
import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backup import DOSJA_BACKUP  # noqa: E402
from config import query  # noqa: E402

DALJA = ROOT / "dokumentimi" / "FarmaBot_Databaza.docx"
TEAL = RGBColor(0x0E, 0x4D, 0x57)
KORAL = RGBColor(0xC8, 0x4A, 0x2E)
GRI = RGBColor(0x5B, 0x6B, 0x73)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin = sec.bottom_margin = Cm(2.0)
st = doc.styles
st["Normal"].font.name = "Calibri"
st["Normal"].font.size = Pt(11)
st["Normal"].paragraph_format.space_after = Pt(6)
for nivel, madhesia, para in ((1, 20, 18), (2, 15, 14), (3, 12.5, 10)):
    h = st[f"Heading {nivel}"]
    h.font.name, h.font.size, h.font.bold = "Cambria", Pt(madhesia), True
    h.font.color.rgb = TEAL if nivel < 3 else RGBColor(0x16, 0x6B, 0x77)
    h.paragraph_format.space_before, h.paragraph_format.space_after = Pt(para), Pt(6)
    h.paragraph_format.keep_with_next = True
    rpr = h.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rf.set(qn(a), "Cambria")
st["Title"].font.name, st["Title"].font.size, st["Title"].font.color.rgb = "Cambria", Pt(36), TEAL


# ---------------------------------------------------------------- ndihmës
def _hije(element, ngjyra: str):
    pr = element.get_or_add_pPr() if hasattr(element, "get_or_add_pPr") else element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), ngjyra)
    pr.append(shd)


def _runs(par, tekst, size=None, ngjyra=None, italic=False):
    for pjese in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", tekst):
        if not pjese:
            continue
        if pjese.startswith("**"):
            r = par.add_run(pjese[2:-2])
            r.bold = True
        elif pjese.startswith("`"):
            r = par.add_run(pjese[1:-1])
            r.font.name, r.font.size, r.font.color.rgb = "Consolas", Pt(9.5), KORAL
            continue
        else:
            r = par.add_run(pjese)
        if size:
            r.font.size = Pt(size)
        if ngjyra:
            r.font.color.rgb = ngjyra
        r.italic = italic


def p(tekst="", stil=None, size=None, ngjyra=None, italic=False, align=None):
    par = doc.add_paragraph(style=stil)
    _runs(par, tekst, size, ngjyra, italic)
    if align is not None:
        par.alignment = align
    return par


def pika(tekst):
    p(tekst, stil="List Bullet").paragraph_format.space_after = Pt(3)


_NR = [0]


def numra(tekst):
    _NR[0] += 1
    par = doc.add_paragraph()
    par.add_run(f"{_NR[0]}.  ").bold = True
    _runs(par, tekst)
    pf = par.paragraph_format
    pf.left_indent, pf.first_line_indent, pf.space_after = Cm(0.9), Cm(-0.6), Pt(3)


def h(tekst, nivel):
    _NR[0] = 0
    doc.add_heading(tekst, nivel)


def kod(tekst):
    rreshtat = tekst.strip("\n").splitlines()
    for i, rr in enumerate(rreshtat):
        par = doc.add_paragraph()
        pf = par.paragraph_format
        pf.space_before = Pt(4) if i == 0 else Pt(0)
        pf.space_after = Pt(6) if i == len(rreshtat) - 1 else Pt(0)
        pf.line_spacing, pf.left_indent = 1.0, Cm(0.3)
        pf.keep_with_next = i < len(rreshtat) - 1 and len(rreshtat) < 25
        r = par.add_run(rr or " ")
        r.font.name, r.font.size = "Consolas", Pt(8.5)
        rf = OxmlElement("w:rFonts")
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(a), "Consolas")
        r._element.get_or_add_rPr().append(rf)
        _hije(par._p, "F1F5F6")


def shenim(tekst, lloji="info"):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    c.width = Cm(16.6)
    _hije(c._tc, {"info": "E6F5F1", "kujdes": "FDE9E4"}[lloji])
    _runs(c.paragraphs[0], tekst)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def tabele(koka, rreshta, gjeresite, size=9.5, kod_kolona=(0,)):
    t = doc.add_table(rows=1, cols=len(koka))
    t.style, t.alignment, t.autofit = "Table Grid", WD_TABLE_ALIGNMENT.CENTER, False
    for i, (c, k) in enumerate(zip(t.rows[0].cells, koka)):
        c.width = Cm(gjeresite[i])
        r = c.paragraphs[0].add_run(k)
        r.bold, r.font.size, r.font.color.rgb = True, Pt(size), RGBColor(0xFF, 0xFF, 0xFF)
        _hije(c._tc, "0E4D57")
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    t.rows[0]._tr.get_or_add_trPr().append(th)
    for j, rresht in enumerate(rreshta):
        for i, (c, v) in enumerate(zip(t.add_row().cells, rresht)):
            c.width = Cm(gjeresite[i])
            par = c.paragraphs[0]
            par.paragraph_format.space_after = Pt(1)
            r = par.add_run(str(v).replace("**", "").replace("`", ""))
            r.font.size = Pt(size if i not in kod_kolona else size - 0.5)
            if i in kod_kolona:
                r.font.name, r.font.color.rgb = "Consolas", TEAL
            if j % 2:
                _hije(c._tc, "F3F6F7")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def faqe_e_re():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def fushe(paragraf, instruksioni):
    r = paragraf.add_run()
    for lloji, tekst in (("begin", None), (None, instruksioni), ("separate", None), (None, "…"), ("end", None)):
        if lloji:
            f = OxmlElement("w:fldChar")
            f.set(qn("w:fldCharType"), lloji)
            r._r.append(f)
        else:
            el = OxmlElement("w:instrText" if tekst == instruksioni else "w:t")
            if tekst == instruksioni:
                el.set(qn("xml:space"), "preserve")
            el.text = tekst
            r._r.append(el)


def madhesia(dosja: Path) -> str:
    if not dosja.exists():
        return "–"
    b = sum(f.stat().st_size for f in dosja.rglob("*") if f.is_file())
    return f"{b / 1024 / 1024:.0f} MB" if b > 1024 * 1024 else f"{b / 1024:.0f} KB"


# ---------------------------------------------------------------- të dhënat live nga databaza
NUMRAT = {r["l"]: r["c"] for r in query(
    "CALL db.labels() YIELD label CALL (label) { MATCH (n) WHERE label IN labels(n) RETURN count(n) AS c } "
    "RETURN label AS l, c")}
LIDHJET_N = {r["t"]: r["c"] for r in query("MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS c")}
KUFIZIMET = query("SHOW CONSTRAINTS YIELD name, labelsOrTypes, properties RETURN name, labelsOrTypes, properties "
                  "ORDER BY name")
INDEKSET = query("SHOW INDEXES YIELD name, type, labelsOrTypes, properties WHERE type <> 'LOOKUP' "
                 "RETURN name, type, labelsOrTypes, properties ORDER BY name")
VERSIONI = query("CALL dbms.components() YIELD name, versions, edition RETURN versions[0] AS v, edition AS e")[0]
LLOGARITE = query("MATCH (l:Llogari) RETURN l.roli AS roli, count(*) AS n, "
                  "sum(CASE WHEN l.email IS NULL THEN 0 ELSE 1 END) AS me_email ORDER BY roli")
NEO4J = ROOT / "neo4j_local" / "server"
BACKUPET = sorted((x for x in DOSJA_BACKUP.iterdir() if x.is_dir()), reverse=True) if DOSJA_BACKUP.exists() else []

# ================================================================ FAQJA E TITULLIT
for _ in range(5):
    doc.add_paragraph()
p("FarmaBot", stil="Title")
p("Databaza Neo4j: udhëzuesi i plotë", size=18, ngjyra=GRI)
p("Ku ruhen përdoruesit, bisedat, reagimet dhe backup-et · si lidhesh · struktura e grafit · query të gatshme",
  size=13, ngjyra=GRI)
doc.add_paragraph()
p(f"Gjendja e databazës më: {date.today().strftime('%d.%m.%Y')} (numrat lexohen nga databaza kur krijohet "
  "dokumenti)", size=11, ngjyra=GRI)
p("Ky dokument nuk përmban fjalëkalime. Ato ndodhen vetëm te skedari .env (kapitulli 3).", size=10, ngjyra=GRI,
  italic=True)
faqe_e_re()
p("Përmbajtja", size=20, ngjyra=TEAL).runs[0].font.name = "Cambria"
fushe(doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')
faqe_e_re()
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run("FarmaBot · Databaza Neo4j · faqja ")
r.font.size, r.font.color.rgb = Pt(9), GRI
fushe(fp, "PAGE")

# ================================================================ 1. PËRMBLEDHJE
h("1. Përmbledhje e shpejtë", 1)
p("FarmaBot i mban **të gjitha** të dhënat e veta në një databazë grafi **Neo4j**: njohuritë mjekësore (simptomat, "
  "ilaçet, gjendjet), tekstet nga datasetet, si dhe të dhënat e njerëzve (llogaritë, profilet, bisedat, reagimet). "
  "Databaza punon lokalisht në këtë kompjuter; asgjë nuk dërgohet jashtë.")
tabele(["Pyetja", "Përgjigjja"], [
    ["Cila databazë është aktive?", "Neo4j lokal, brenda projektit (neo4j_local\\server)"],
    ["Versioni", f"Neo4j {VERSIONI['v']} ({VERSIONI['e']})"],
    ["Adresa për programin", "bolt://127.0.0.1:7687 (vetëm nga ky kompjuter)"],
    ["Adresa për shfletuesin", "http://localhost:7474 (Neo4j Browser)"],
    ["Emri i databazës", "neo4j"],
    ["Përdoruesi / fjalëkalimi", "neo4j / te skedari .env, rreshti NEO4J_PASSWORD"],
    ["Ku janë skedarët e databazës?", "chatbot_industri\\neo4j_local\\server\\data\\databases\\neo4j"],
    ["Ku ruhen përdoruesit?", "Nyjet (:Llogari) dhe (:Person) në databazë (kapitulli 6)"],
    ["Ku ruhen backup-et?", f"{DOSJA_BACKUP} (kapitulli 9)"],
    ["Si niset?", "Ikona FarmaBot në Desktop (nis_farmabot.pyw) e nis vetë"],
], [5.6, 11.0], kod_kolona=())

h("1.1 Dy pjesët e databazës", 2)
p("Databaza ka dy pjesë që jetojnë në të njëjtin graf:")
pika("**Njohuritë** (nuk ndryshojnë nga përdoruesit): `Simptome`, `Fraze`, `Barna`, `Gjendje`, `Chunk`. Ato "
     "krijohen nga skedarët JSON te `data\\` dhe mund të rikrijohen kurdo (`python ngarko_grafin.py`).")
pika("**Të dhënat e njerëzve** (krijohen gjatë përdorimit): `Llogari`, `Person`, `Bisede`, `Mesazh`, `Reagim`. "
     "Këto ekzistojnë **vetëm** në databazë, prandaj backup-i është i rëndësishëm për to.")
GRUPI = {"Simptome": "njohuri", "Fraze": "njohuri", "Barna": "njohuri", "Gjendje": "njohuri", "Chunk": "njohuri",
         "Llogari": "njerëzit", "Person": "njerëzit", "Bisede": "njerëzit", "Mesazh": "njerëzit", "Reagim": "njerëzit"}
PERSHKRIMI = {
    "Simptome": "Një simptomë (dhimbje koke, kollë...) me këshillat dhe shenjat e alarmit",
    "Fraze": "Një mënyrë si e shkruajnë njerëzit simptomën, me embedding (vektor 1024 numrash)",
    "Barna": "Një ilaç pa recetë: doza, doza maksimale, paralajmërimet, emrat tregtarë",
    "Gjendje": "Një gjendje shëndetësore (shtatzëni, ulçerë, astmë, fëmijë nën 12 vjeç...)",
    "Chunk": "Një copë teksti nga datasetet (MedlinePlus, openFDA) ose PDF, me embedding",
    "Llogari": "Llogaria e hyrjes: emri i përdoruesit, email-i, hash-i i fjalëkalimit, roli",
    "Person": "Profili shëndetësor i personit: mosha, shënimet, gjendjet",
    "Bisede": "Një bisedë në listën majtas (titulli, konteksti)",
    "Mesazh": "Një mesazh i bisedës (i personit ose i botit)",
    "Reagim": "Një vlerësim 👍/👎 për një përgjigje të botit",
}
tabele(["Nyja", "Pjesa", "Çfarë është", "Sa ka"],
       [[k, GRUPI.get(k, "–"), PERSHKRIMI.get(k, "–"), NUMRAT.get(k, 0)] for k in
        ["Simptome", "Fraze", "Barna", "Gjendje", "Chunk", "Llogari", "Person", "Bisede", "Mesazh", "Reagim"]],
       [2.4, 2.0, 10.4, 1.8], kod_kolona=(0,))

# ================================================================ 2. NË DISK
h("2. Ku ndodhet databaza në disk", 1)
p("Neo4j është instaluar brenda dosjes së projektit, që projekti të jetë i plotë në një vend:")
tabele(["Dosja / skedari", "Çfarë përmban", "Madhësia"], [
    ["neo4j_local\\server\\", "Programi Neo4j (Community Server)", madhesia(NEO4J / "lib")],
    ["neo4j_local\\jre\\", "Java që përdor Neo4j (nuk duhet Java e instaluar veçmas)", madhesia(ROOT / "neo4j_local" / "jre")],
    ["…\\server\\data\\databases\\neo4j\\", "**Të dhënat** e databazës FarmaBot (nyjet, lidhjet, indekset)",
     madhesia(NEO4J / "data" / "databases" / "neo4j")],
    ["…\\server\\data\\databases\\system\\", "Databaza e sistemit të Neo4j (përdoruesit e Neo4j, jo të FarmaBot-it)",
     madhesia(NEO4J / "data" / "databases" / "system")],
    ["…\\server\\data\\transactions\\", "Regjistri i transaksioneve (për rikuperim pas ndërprerjeve)",
     madhesia(NEO4J / "data" / "transactions")],
    ["…\\server\\conf\\neo4j.conf", "Konfigurimi: portat, memoria, dosjet", "–"],
    ["…\\server\\logs\\", "Log-et e brendshme të Neo4j (debug.log)", madhesia(NEO4J / "logs")],
    ["chatbot_industri\\logs\\neo4j.out.log / .err.log", "Çfarë shkruan Neo4j kur niset nga ikona", "–"],
], [6.2, 8.2, 2.2], kod_kolona=(0,))
shenim("Mos i kopjo, fshi ose ndrysho skedarët te `data\\databases` me dorë ndërkohë që Neo4j punon. Për kopje "
       "përdor backup-in (kapitulli 9).", "kujdes")
h("2.1 Konfigurimi (neo4j.conf)", 2)
tabele(["Cilësimi", "Vlera", "Kuptimi"], [
    ["server.default_listen_address", "127.0.0.1", "Dëgjon vetëm nga ky kompjuter (jo nga rrjeti)"],
    ["porti Bolt", "7687", "Lidhja e programit (Python)"],
    ["porti HTTP", "7474", "Neo4j Browser në shfletues"],
    ["server.memory.heap.max_size", "1g", "Memoria maksimale e Java-s"],
    ["server.memory.pagecache.size", "512m", "Memoria për të mbajtur databazën në RAM"],
], [5.6, 2.4, 8.6], kod_kolona=(0, 1))

# ================================================================ 3. LIDHJA
h("3. Si lidhesh me databazën", 1)
h("3.1 Skedari .env", 2)
p("Të dhënat e lidhjes janë te `chatbot_industri\\.env` (hape me Notepad). Ky skedar **nuk** futet në Git.")
kod("""NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<fjalëkalimi është këtu>
NEO4J_DATABASE=neo4j
NEO4J_TRANSPORT=bolt""")
p("Po aty ka edhe të dhënat e Neo4j Aura (cloud, `NEO4J_AURA_*`), që nuk përdoret më si databazë aktive, "
  "dhe të dhënat e Gmail-it (`SMTP_*`) për email-et e rivendosjes.")
p("Kodi lexon `.env` te `config.py`; çdo skedar tjetër përdor funksionin `query()` prej andej:")
kod("""from config import query
query("MATCH (l:Llogari) RETURN l.perdoruesi AS emri, l.roli AS roli")""")
h("3.2 Neo4j Browser (pa kod)", 2)
for t in ["Sigurohu që FarmaBot është nisur (ikona në Desktop).",
          "Hap në shfletues **http://localhost:7474**.",
          "Connect URL: `bolt://localhost:7687`, Username: `neo4j`, Password: nga `.env`.",
          "Shkruaj një query në kutinë sipër (p.sh. `MATCH (n) RETURN labels(n), count(*)`) dhe shtyp Ctrl+Enter.",
          "Për të parë grafin: `CALL db.schema.visualization()`."]:
    numra(t)
h("3.3 cypher-shell (rreshti i komandave)", 2)
kod("""cd C:\\Users\\Admin\\chatbot_industri\\neo4j_local\\server
set JAVA_HOME=C:\\Users\\Admin\\chatbot_industri\\neo4j_local\\jre
bin\\cypher-shell.bat -u neo4j -p <fjalekalimi> "MATCH (n) RETURN count(n);\"""")
h("3.4 Nisja dhe ndalimi", 2)
tabele(["Veprimi", "Si"], [
    ["Nis gjithçka", "Ikona FarmaBot në Desktop (nis_farmabot.pyw): Ollama → Neo4j → aplikacioni"],
    ["Ndal", "“Ndal FarmaBot” në dosjen e projektit (ndal_farmabot.pyw): ndalon aplikacionin dhe Neo4j"],
    ["Kontrollo nëse punon", "netstat -ano | findstr 7687   (duhet LISTENING)"],
    ["Nis vetëm Neo4j", "neo4j_local\\server\\bin\\neo4j.bat console  (me JAVA_HOME si më sipër)"],
], [4.2, 12.4], kod_kolona=())

# ================================================================ 4. STRUKTURA
h("4. Struktura e grafit", 1)
kod("""(:Fraze)-[:I_PERKET]->(:Simptome)-[:TRAJTOHET_ME {rendi}]->(:Barna)
(:Barna)-[:KUNDERINDIKOHET_PER]->(:Gjendje)      (:Barna)-[:KUJDES_ME]->(:Gjendje)
(:Chunk)-[:PERSHKRUAN]->(:Barna)

(:Llogari)-[:ESHTE]->(:Person)-[:KA_GJENDJE]->(:Gjendje)
(:Person)-[:KA_BISEDE]->(:Bisede)-[:PERMBAN]->(:Mesazh)
(:Person)-[:DERGOI]->(:Mesazh)-[:PER_SIMPTOMEN]->(:Simptome)
                     (:Mesazh)-[:SUGJEROI]->(:Barna)
(:Reagim)   (e pavarur; ruan emrin e përdoruesit si tekst)""")
h("4.1 Lidhjet", 2)
LIDHJET = [
    ("I_PERKET", "Fraze → Simptome", "Fraza është një mënyrë për të thënë këtë simptomë"),
    ("TRAJTOHET_ME", "Simptome → Barna", "Ilaçi sugjerohet për simptomën; `rendi` = radha e preferencës"),
    ("KUNDERINDIKOHET_PER", "Barna → Gjendje", "Ilaçi NUK jepet për këtë gjendje"),
    ("KUJDES_ME", "Barna → Gjendje", "Ilaçi jepet me kujdes / paralajmërim"),
    ("PERSHKRUAN", "Chunk → Barna", "Teksti nga datasetet flet për këtë ilaç"),
    ("ESHTE", "Llogari → Person", "Llogaria i përket këtij profili"),
    ("KA_GJENDJE", "Person → Gjendje", "Personi ka këtë gjendje (shtatzëni, ulçerë...)"),
    ("KA_BISEDE", "Person → Bisede", "Bisedat e personit"),
    ("PERMBAN", "Bisede → Mesazh", "Mesazhet e bisedës"),
    ("DERGOI", "Person → Mesazh", "Kush e dërgoi mesazhin (historia e vjetër, statistikat)"),
    ("PER_SIMPTOMEN", "Mesazh → Simptome", "Simptoma që bota gjeti te mesazhi"),
    ("SUGJEROI", "Mesazh → Barna", "Ilaçi që bota sugjeroi në atë përgjigje"),
]
tabele(["Lidhja", "Nga → te", "Kuptimi", "Sa ka"],
       [[a, b, c, LIDHJET_N.get(a, 0)] for a, b, c in LIDHJET], [3.8, 3.6, 7.4, 1.8], kod_kolona=(0,))

# ================================================================ 5. NYJET E NJOHURIVE
h("5. Njohuritë: simptomat, ilaçet, gjendjet, tekstet", 1)
NYJET_NJOHURI = [
    ("Simptome", "data/njohurite.json → ngarko_grafin.py", [
        ("id", "Çelësi unik, p.sh. dhimbje_koke"), ("emer", "Emri që shfaqet"), ("fjale_kyce", "Fjalë për kërkimin"),
        ("pershkrim / info", "Përshkrimi"), ("keshilla", "Këshillat pa ilaç"),
        ("shenja_alarmi", "Kur duhet mjeku"), ("kerkon_mjek", "true = gjithmonë te mjeku")]),
    ("Fraze", "data/njohurite.json (frazat) + trajnimi/meso.py", [
        ("tekst", "Fraza, p.sh. “më çan koka”"), ("embedding", "Vektori i kuptimit (bge-m3, 1024 numra)")]),
    ("Barna", "data/njohurite.json; ndryshohen edhe te Admin → Ilaçet", [
        ("id", "Çelësi unik, p.sh. paracetamol"), ("emer", "Emri, p.sh. Paracetamol 500 mg"),
        ("lende_aktive / forma", "Lënda aktive dhe forma"), ("doza / doza_maks", "Doza e zakonshme dhe maksimale"),
        ("si_merret / kohezgjatja", "Udhëzimet"), ("paralajmerime / efekte_anesore", "Paralajmërimet"),
        ("emra_tregtare", "Emrat në farmaci")]),
    ("Gjendje", "data/njohurite.json", [("id", "p.sh. shtatzeni"), ("emer", "p.sh. Shtatzëni")]),
    ("Chunk", "shkarko_datasetet.py → ngarko_burimet.py; ngarko_pdf.py", [
        ("tekst", "Copa e tekstit"), ("embedding", "Vektori i kuptimit"), ("lloji", "openfda / medlineplus / pdf"),
        ("burimi / seksioni / url", "Nga erdhi"), ("gjuha", "en / sq")]),
]
for emri, burimi_, fushat in NYJET_NJOHURI:
    h(f"5.{NYJET_NJOHURI.index((emri, burimi_, fushat)) + 1} (:{emri})  ·  {NUMRAT.get(emri, 0)} nyje", 2)
    p(f"Krijohet nga: `{burimi_}`")
    tabele(["Fusha", "Kuptimi"], [list(x) for x in fushat], [4.6, 12.0])
shenim("Burimi i vërtetë i njohurive është `data\\njohurite.json`. Nëse databaza fshihet, njohuritë rikrijohen me "
       "`python ngarko_grafin.py` (dhe tekstet me `python ngarko_burimet.py`). Të dhënat e njerëzve NUK rikrijohen "
       "kështu: për to duhet backup-i.")

# ================================================================ 6. PËRDORUESIT
h("6. Ku ruhen përdoruesit", 1)
p("Çdo përdorues ka **dy nyje** të lidhura: llogarinë e hyrjes dhe profilin shëndetësor.")
kod("""(:Llogari {perdoruesi: "admin", email: "...", roli: "admin", hash, kripe, ...})
        -[:ESHTE]->
(:Person {id: "c0109e51-...", mosha, shenime, krijuar, perditesuar})-[:KA_GJENDJE]->(:Gjendje)""")
h("6.1 (:Llogari): llogaria e hyrjes", 2)
p("Skedari që e menaxhon: `llogarite.py`.")
tabele(["Fusha", "Kuptimi"], [
    ["perdoruesi", "Emri i përdoruesit (unik, shkronja të vogla)"],
    ["email", "Email-i (unik); përdoret për hyrje dhe rivendosje"],
    ["hash", "Hash-i PBKDF2-SHA256 i fjalëkalimit (200 000 iteracione). Fjalëkalimi NUK ruhet kurrë si tekst"],
    ["kripe", "Kripa e rastësishme e hash-it (e ndryshme për çdo llogari)"],
    ["roli", "admin ose perdorues"],
    ["krijuar / hyrja_fundit", "Kur u krijua llogaria / hyrja e fundit"],
    ["rivendos_hash", "Hash-i SHA-256 i token-it të rivendosjes (jo vetë token-i)"],
    ["rivendos_skadon / rivendos_derguar", "Skadimi (30 minuta) dhe ora e dërgimit të email-it"],
], [5.0, 11.6])
p("Gjendja aktuale e llogarive:")
tabele(["Roli", "Llogari", "Me email"], [[r["roli"], r["n"], r["me_email"]] for r in LLOGARITE], [5, 4, 4])
shenim("Askush, as admini, nuk mund ta lexojë fjalëkalimin e një përdoruesi: në databazë ka vetëm hash. Nëse "
       "harrohet, përdoret “Ke harruar fjalëkalimin?” ose admini vendos një fjalëkalim të ri te Admin → Përdoruesit. "
       "Llogaria **admin** krijohet vetë në nisje nga `ADMIN_USERNAME` / `ADMIN_PASSWORD` te `.env` nëse nuk ekziston.")
h("6.2 (:Person): profili shëndetësor", 2)
p("Skedari: `perdoruesit.py`. Plotësohet te Cilësimet → Profili shëndetësor.")
tabele(["Fusha", "Kuptimi"], [
    ["id", "Identifikues i rastësishëm (UUID)"], ["emer", "Emri (opsional)"], ["mosha", "Mosha (për dozat e fëmijëve)"],
    ["shenime", "Shënime të lira (p.sh. alergjitë)"], ["krijuar / perditesuar", "Datat"],
    ["-[:KA_GJENDJE]->", "Gjendjet: shtatzëni, ulçerë, astmë, hipertension..."],
], [5.0, 11.6])
h("6.3 Fshirja e një përdoruesi", 2)
p("Admin → Përdoruesit → Fshi (ose `llogarite.fshi_llogari(\"emri\")`) fshin llogarinë, profilin, bisedat dhe "
  "mesazhet e tij. Admini i fundit nuk mund të fshihet.")

# ================================================================ 7. BISEDAT
h("7. Ku ruhen bisedat dhe mesazhet", 1)
p("Skedari: `bisedat.py`. Çdo bisedë e listës majtas është një nyje `(:Bisede)`; çdo mesazh është `(:Mesazh)`.")
tabele(["Nyja.fusha", "Kuptimi"], [
    ["Bisede.id / titull", "Identifikuesi dhe titulli (merret nga mesazhi i parë; mund të riemërtohet)"],
    ["Bisede.krijuar / perditesuar", "Datat (lista renditet sipas perditesuar)"],
    ["Bisede.konteksti", "JSON: simptomat, ilaçet, pyetja sqaruese në pritje, që biseda të vazhdojë kur rihapet"],
    ["Bisede.fshire / fshire_me", "true dhe data kur përdoruesi e fshiu bisedën: zhduket nga lista e tij, por mbetet "
                                  "me mesazhet për administratorin (Admin → Përdoruesit → Bisedat)"],
    ["Mesazh.roli", "user (personi) ose assistant (bota)"],
    ["Mesazh.tekst / ora", "Teksti dhe koha"],
    ["Mesazh.te_dhena", "JSON: kartat e ilaçeve, hapat e mendimit, burimet; për t'i rishfaqur"],
], [5.4, 11.2], kod_kolona=(0,))
p("Kur përdoruesi fshin një bisedë, ajo vetëm shënohet `fshire = true` (nuk fshihet nga databaza). Përdoruesi nuk e "
  "sheh, nuk e hap dhe nuk e vazhdon dot më; admini e sheh me shënimin “Fshirë nga përdoruesi”. Bisedat fshihen "
  "përfundimisht vetëm kur fshihet llogaria (nga vetë personi ose nga admini), ose me `bisedat.fshi_perfundimisht()`.")
p(f"Aktualisht: {NUMRAT.get('Bisede', 0)} biseda me {NUMRAT.get('Mesazh', 0)} mesazhe. Vizitorët (pa llogari) "
  "**nuk** ruhen në databazë: biseda e tyre mbetet vetëm në sesionin e shfletuesit.")

# ================================================================ 8. REAGIMET
h("8. Reagimet 👍/👎 dhe trajnimi", 1)
p("Skedari: `trajnimi/reagimet.py`. Çdo klikim 👍 ose 👎 krijon një nyje `(:Reagim)`.")
tabele(["Fusha", "Kuptimi"], [
    ["vlera", "1 = 👍, -1 = 👎"], ["arsye", "nuk_kuptoi / ilac_gabim / e_paqarte / tjeter"], ["koment", "Teksti i personit"],
    ["pyetja / pergjigjja", "Mesazhi dhe përgjigjja e botit"], ["simptomat", "Simptomat që gjeti bota"],
    ["perdoruesi", "Emri i përdoruesit (bosh për vizitorët)"], ["statusi", "hapur / zgjidhur"],
    ["zgjidhja", "Çfarë bëri admini (p.sh. “U mësua si: grip_ftohje”)"], ["ora", "Koha"],
], [4.4, 12.2])
p("Jashtë databazës, në dosjen `trajnimi\\`: `rastet.json` (grupi i provës), `raportet\\` (një raport për çdo "
  "vlerësim) dhe `mesimet.json` (regjistri i frazave të mësuara). Detajet: dokumentimi kryesor, kapitulli 15.")

# ================================================================ 9. BACKUP
h("9. Backup-i: ku ruhet dhe si rikthehet", 1)
p(f"Backup-et ruhen në **{DOSJA_BACKUP}**, një dosje për çdo backup me emrin datë_orë:")
kod(f"""{DOSJA_BACKUP}\\
   2026-11-22_02-41-34\\
      databaza.json     ← të gjitha nyjet dhe lidhjet (JSON)
      databaza.cypher   ← skript që e rikrijon databazën kudo
      LEXOMË.txt        ← udhëzimet dhe numri i nyjeve/lidhjeve""")
if BACKUPET:
    p("Backup-et që ekzistojnë tani:")
    tabele(["Dosja", "Madhësia"], [[b.name, madhesia(b)] for b in BACKUPET[:12]], [8, 4])
shenim("Backup-i përmban të dhëna shëndetësore dhe hash-et e fjalëkalimeve. Mbaje në vend të sigurt; mos e dërgo me "
       "email. Bëje backup para çdo ndryshimi të madh dhe të paktën një herë në javë.", "kujdes")
h("9.1 Si bëhet backup", 2)
tabele(["Mënyra", "Hapat"], [
    ["Nga faqja (më e lehta)", "Hyr si admin → Paneli i administratorit → Backup → “Bëj backup tani”"],
    ["Nga rreshti i komandave", "venv_chatbot\\Scripts\\python backup.py"],
    ["Kopje e plotë e skedarëve (dump)", "Ndal FarmaBot, pastaj: neo4j-admin database dump neo4j --to-path=<dosja>"],
], [5.2, 11.4], kod_kolona=())
h("9.2 Si rikthehet një backup", 2)
p("**Kujdes:** rikthimi fshin gjithçka që ka databaza tani dhe vendos përmbajtjen e backup-it.")
for t in ["Bëj fillimisht një backup të gjendjes aktuale (për siguri).",
          "Hap Neo4j Browser (http://localhost:7474) dhe hyr.",
          "Hap `databaza.cypher` të backup-it me Notepad, kopjo gjithë përmbajtjen, ngjite te Browser-i dhe ekzekutoje. "
          "Ose me cypher-shell: `bin\\cypher-shell.bat -u neo4j -p <fjalekalimi> -f <rruga>\\databaza.cypher`.",
          "Rinis FarmaBot (Ndal FarmaBot → FarmaBot), që aplikacioni të rikrijojë cache-t dhe kufizimet."]:
    numra(t)
p("Për një dump të bërë me `neo4j-admin`: me Neo4j të ndalur, "
  "`neo4j-admin database load neo4j --from-path=<dosja> --overwrite-destination=true`.")
h("9.3 Kopje në një Neo4j tjetër", 2)
p("`python backup.py --lokal` kopjon gjithë databazën në një Neo4j tjetër (p.sh. Neo4j Desktop), sipas "
  "`NEO4J_LOCAL_URI / _USERNAME / _PASSWORD` te `.env`. Fillimisht u përdor për të kaluar nga Aura në lokal.")

# ================================================================ 10. KUFIZIMET DHE INDEKSET
h("10. Kufizimet dhe indekset", 1)
p("**Kufizimet** (constraints) garantojnë që një vlerë është unike (p.sh. dy llogari nuk mund të kenë të njëjtin "
  "email). **Indekset** e bëjnë kërkimin të shpejtë; indekset **VECTOR** përdoren për kërkimin sipas kuptimit.")
tabele(["Kufizimi", "Nyja", "Fusha unike"],
       [[k["name"], ", ".join(k["labelsOrTypes"] or []), ", ".join(k["properties"] or [])] for k in KUFIZIMET],
       [5.2, 4.4, 7.0])
tabele(["Indeksi", "Lloji", "Nyja", "Fusha"],
       [[i["name"], i["type"], ", ".join(i["labelsOrTypes"] or []), ", ".join(i["properties"] or [])] for i in INDEKSET],
       [5.0, 2.6, 4.0, 5.0])
p("Kufizimet krijohen vetë kur niset aplikacioni (`krijo_skemen()` te çdo modul) dhe gjatë ngarkimit të njohurive.")

# ================================================================ 11. QUERY
h("11. Query të gatshme", 1)
QUERY = [
    ("Sa nyje ka nga çdo lloj", "MATCH (n) RETURN labels(n)[0] AS lloji, count(*) AS sa ORDER BY sa DESC"),
    ("Të gjithë përdoruesit (pa hash)", "MATCH (l:Llogari) RETURN l.perdoruesi, l.email, l.roli, l.krijuar, "
                                         "l.hyrja_fundit ORDER BY l.krijuar"),
    ("Profili i një përdoruesi", "MATCH (l:Llogari {perdoruesi:'admin'})-[:ESHTE]->(p:Person)\n"
                                 "OPTIONAL MATCH (p)-[:KA_GJENDJE]->(g) RETURN p.mosha, p.shenime, collect(g.emer)"),
    ("Bisedat e një përdoruesi", "MATCH (:Llogari {perdoruesi:'admin'})-[:ESHTE]->(:Person)-[:KA_BISEDE]->(b)\n"
                                 "RETURN b.titull, b.perditesuar ORDER BY b.perditesuar DESC"),
    ("Mesazhet e një bisede", "MATCH (b:Bisede {titull:'...'})-[:PERMBAN]->(m) RETURN m.roli, m.tekst ORDER BY m.ora"),
    ("Ankesat e hapura", "MATCH (r:Reagim {statusi:'hapur'}) RETURN r.pyetja, r.arsye, r.koment, r.ora ORDER BY r.ora DESC"),
    ("Ilaçet për një simptomë", "MATCH (:Simptome {id:'dhimbje_koke'})-[t:TRAJTOHET_ME]->(b) RETURN b.emer ORDER BY t.rendi"),
    ("Kush nuk duhet ta marrë një ilaç", "MATCH (:Barna {id:'ibuprofen'})-[:KUNDERINDIKOHET_PER]->(g) RETURN g.emer"),
    ("Ilaçet më të sugjeruara", "MATCH (:Mesazh)-[:SUGJEROI]->(b) RETURN b.emer, count(*) AS sa ORDER BY sa DESC LIMIT 10"),
    ("Pamja e strukturës", "CALL db.schema.visualization()"),
]
for titulli, q in QUERY:
    p(f"**{titulli}**").paragraph_format.space_after = Pt(0)
    kod(q)
shenim("Query-t që ndryshojnë të dhënat (`CREATE`, `SET`, `DELETE`) bëji vetëm pasi ke bërë backup. Për përdoruesit "
       "dhe ilaçet përdor Panelin e administratorit, jo Browser-in.", "kujdes")

# ================================================================ 12. JASHTË NEO4J
h("12. Të dhëna që ruhen jashtë Neo4j", 1)
tabele(["Skedari", "Përmbajtja"], [
    [".env", "Fjalëkalimet: Neo4j, admin-i fillestar, Gmail (SMTP), çelësi i sesioneve"],
    ["data\\njohurite.json", "Burimi i njohurive (simptomat, frazat, ilaçet, gjendjet)"],
    ["data\\fjalori_shqip.json / fjalori_anglisht.json", "Fjalorët e shqipes së folur dhe të anglishtes"],
    ["data\\burime\\, data\\pdf\\", "Datasetet e shkarkuara dhe PDF-të"],
    ["trajnimi\\", "Grupi i provës, raportet e vlerësimit, regjistri i mësimeve"],
    ["logs\\emailet.log", "Lidhjet e rivendosjes kur SMTP nuk është konfiguruar"],
    ["logs\\*.log", "Log-et e aplikacionit, Neo4j dhe Ollama"],
], [6.6, 10.0], kod_kolona=(0,))

# ================================================================ 13. AURA
h("13. Neo4j Aura (cloud), opsionale", 1)
p("Në fillim projekti përdori Neo4j Aura (instanca falas në cloud). Tani databaza aktive është ajo lokale; "
  "të dhënat e Aura-s janë ende te `.env` (`NEO4J_AURA_*`). Për t'u kthyer te Aura: kopjo vlerat e Aura-s te "
  "`NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD / NEO4J_DATABASE`, vendos `NEO4J_TRANSPORT=auto` dhe rinis. "
  "Instanca falas e Aura-s vihet në pauzë pas disa ditësh pa përdorim dhe rinisej te console.neo4j.io.")

# ================================================================ 14. PROBLEMET
h("14. Problemet e shpeshta", 1)
tabele(["Problemi", "Zgjidhja"], [
    ["ServiceUnavailable / connection refused", "Neo4j nuk punon: nis FarmaBot nga ikona; shiko logs\\neo4j.err.log"],
    ["AuthError / Unauthorized", "Fjalëkalimi te .env nuk përputhet me atë të Neo4j"],
    ["Porti 7687 i zënë", "netstat -ano | findstr 7687; ndal procesin e vjetër (Ndal FarmaBot)"],
    ["Neo4j nuk niset pas fikjes së papritur", "Shiko neo4j_local\\server\\logs\\debug.log; zakonisht mjafton rinisja"],
    ["Fjalëkalimi i Neo4j u harrua", "Shiko .env. Ose: ndal Neo4j, `neo4j-admin dbms set-initial-password <i_ri>` "
                                      "(vetëm kur databaza system është e re) dhe përditëso .env"],
], [5.6, 11.0], kod_kolona=())

doc.core_properties.title = "FarmaBot: databaza Neo4j"
doc.core_properties.author = "FarmaBot"
doc.save(DALJA)
print(f"U ruajt: {DALJA}")
