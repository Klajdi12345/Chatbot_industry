"""Krijon dokumentimi/FarmaBot_Dokumentimi.docx: dokumenti i plotë për ta mësuar sistemin.

Tabelat e funksioneve dhe pjesët e kodit lexohen drejt nga kodi burimor (ast), që dokumenti të mos dalë
i vjetër kur ndryshon kodi. Shembujt e bisedës vijnë nga dokumentimi/shembuj_bisede.json dhe
shembull_mendimi.json (të gjeneruar nga bota reale). Figurat janë slajdet e prezantimit.

Ekzekuto me një Python që ka python-docx:   python dokumentimi/krijo_dokumentimin.py
PDF-ja dhe tabela e përmbajtjes krijohen pastaj me Word (shiko eksporto_pdf.ps1).
"""
import ast
import json
import re
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT  # noqa: F401
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
DOK = ROOT / "dokumentimi"
DALJA = DOK / "FarmaBot_Dokumentimi.docx"

TEAL = RGBColor(0x0E, 0x4D, 0x57)
KORAL = RGBColor(0xC8, 0x4A, 0x2E)
GRI = RGBColor(0x5B, 0x6B, 0x73)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin = sec.bottom_margin = Cm(2.0)

# ---------------------------------------------------------------- stilet
st = doc.styles
st["Normal"].font.name = "Calibri"
st["Normal"].font.size = Pt(11)
st["Normal"].paragraph_format.space_after = Pt(6)
st["Normal"].paragraph_format.line_spacing = 1.12
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


def _hije(element, ngjyra: str):
    pr = element.get_or_add_pPr() if hasattr(element, "get_or_add_pPr") else element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), ngjyra)
    pr.append(shd)


def p(tekst: str = "", stil: str | None = None, bold_fillim: str | None = None, ngjyra=None, size=None,
      italic=False, align=None):
    """Paragraf; **bold** dhe `kod` brenda tekstit kthehen në formatim."""
    par = doc.add_paragraph(style=stil)
    if bold_fillim:
        r = par.add_run(bold_fillim)
        r.bold = True
        if ngjyra:
            r.font.color.rgb = ngjyra
    for pjese in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", tekst):
        if not pjese:
            continue
        if pjese.startswith("**"):
            r = par.add_run(pjese[2:-2])
            r.bold = True
        elif pjese.startswith("`"):
            r = par.add_run(pjese[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(9.5)
            r.font.color.rgb = KORAL
        else:
            r = par.add_run(pjese)
        if size:
            r.font.size = Pt(size)
        if italic:
            r.italic = True
        if ngjyra and not pjese.startswith("`"):
            r.font.color.rgb = ngjyra
    if align:
        par.alignment = align
    return par


def pika(tekst: str, nivel: int = 0):
    par = p(tekst, stil="List Bullet" if nivel == 0 else "List Bullet 2")
    par.paragraph_format.space_after = Pt(3)
    return par


_NR = [0]


def rinis_numrat():
    _NR[0] = 0


def numra(tekst: str):
    _NR[0] += 1
    par = p(tekst, bold_fillim=f"{_NR[0]}.  ")
    pf = par.paragraph_format
    pf.left_indent, pf.first_line_indent, pf.space_after = Cm(0.9), Cm(-0.6), Pt(3)
    return par


def kod(tekst: str, gjuha: str = ""):
    """Bllok kodi: Consolas 9 pt, sfond gri i lehtë, rreshtat bashkë."""
    rreshtat = tekst.strip("\n").splitlines()
    for i, rr in enumerate(rreshtat):
        par = doc.add_paragraph()
        pf = par.paragraph_format
        pf.space_before = Pt(4) if i == 0 else Pt(0)
        pf.space_after = Pt(6) if i == len(rreshtat) - 1 else Pt(0)
        pf.line_spacing = 1.0
        pf.left_indent = Cm(0.3)
        pf.keep_with_next = i < len(rreshtat) - 1 and len(rreshtat) < 25
        r = par.add_run(rr if rr else " ")
        r.font.name, r.font.size = "Consolas", Pt(8.5)
        rpr = r._element.get_or_add_rPr()
        rf = OxmlElement("w:rFonts")
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(a), "Consolas")
        rpr.append(rf)
        _hije(par._p, "F1F5F6")


def shenim(tekst: str, lloji: str = "info"):
    ngjyra = {"info": "E6F5F1", "kujdes": "FDE9E4"}[lloji]
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    c.width = Cm(16.6)
    _hije(c._tc, ngjyra)
    c.paragraphs[0].text = ""
    par = c.paragraphs[0]
    for pjese in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", tekst):
        if pjese.startswith("**"):
            par.add_run(pjese[2:-2]).bold = True
        elif pjese.startswith("`"):
            r = par.add_run(pjese[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(9.5)
        elif pjese:
            par.add_run(pjese)
    par.paragraph_format.space_after = Pt(2)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def tabele(koka: list[str], rreshta: list[list[str]], gjeresite: list[float], size: float = 9.5, kod_kolona=(0,)):
    t = doc.add_table(rows=1, cols=len(koka))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, (c, k) in enumerate(zip(t.rows[0].cells, koka)):
        c.width = Cm(gjeresite[i])
        c.paragraphs[0].text = ""
        r = c.paragraphs[0].add_run(k)
        r.bold, r.font.size, r.font.color.rgb = True, Pt(size), RGBColor(0xFF, 0xFF, 0xFF)
        _hije(c._tc, "0E4D57")
    # koka përsëritet në çdo faqe
    trpr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trpr.append(th)
    for j, rresht in enumerate(rreshta):
        cells = t.add_row().cells
        for i, (c, v) in enumerate(zip(cells, rresht)):
            c.width = Cm(gjeresite[i])
            par = c.paragraphs[0]
            par.paragraph_format.space_after = Pt(1)
            r = par.add_run(v)
            r.font.size = Pt(size if i not in kod_kolona else size - 0.5)
            if i in kod_kolona:
                r.font.name = "Consolas"
                r.font.color.rgb = TEAL
            if j % 2:
                _hije(c._tc, "F3F6F7")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(emri: str, titulli: str, gjeresia=16.5):
    doc.add_picture(str(DOK / "figurat" / emri), width=Cm(gjeresia))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p(titulli, ngjyra=GRI, size=9.5, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)


def faqe_e_re():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def fushe(paragraf, instruksioni: str):
    r = paragraf.add_run()
    for lloji, tekst in (("begin", None), (None, instruksioni), ("separate", None), (None, "…"), ("end", None)):
        if lloji:
            f = OxmlElement("w:fldChar")
            f.set(qn("w:fldCharType"), lloji)
            r._r.append(f)
        elif tekst == instruksioni:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = instruksioni
            r._r.append(it)
        else:
            t = OxmlElement("w:t")
            t.text = tekst
            r._r.append(t)


# ---------------------------------------------------------------- kodi burimor
def burimi(skedari: str) -> str:
    return (ROOT / skedari).read_text(encoding="utf-8")


def funksioni(skedari: str, emri: str) -> str:
    """Kodi i plotë i një funksioni nga skedari (për shembujt)."""
    s = burimi(skedari)
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == emri:
            return ast.get_source_segment(s, n)
    raise KeyError(emri)


def funksionet(skedari: str) -> list[dict]:
    s = burimi(skedari)
    dalja = []
    for n in ast.parse(s).body:
        if isinstance(n, ast.FunctionDef):
            args = []
            for a, d in zip(n.args.args, [None] * (len(n.args.args) - len(n.args.defaults)) + n.args.defaults):
                args.append(a.arg + (f": {ast.unparse(a.annotation)}" if a.annotation else "")
                            + (f" = {ast.unparse(d)}" if d is not None else ""))
            if n.args.kwarg:
                args.append("**" + n.args.kwarg.arg)
            dalja.append({"emri": n.name, "merr": ", ".join(args) or "–",
                          "kthen": ast.unparse(n.returns) if n.returns else "–",
                          "doc": (ast.get_docstring(n) or "").strip()})
        elif isinstance(n, ast.ClassDef):
            dalja.append({"emri": n.name, "merr": "(klasë)", "kthen": "–", "doc": (ast.get_docstring(n) or "").strip()})
    return dalja


# Përshkrime për funksionet pa docstring (ose me docstring shumë teknik)
PERSHKRIME = {
    "_uri": "Lexon NEO4J_URI nga .env. Ngre RuntimeError nëse mungon.",
    "get_driver": "Krijon një herë (lru_cache) drajverin Bolt të Neo4j me përdoruesin/fjalëkalimin e .env.",
    "_query_https": "Dërgon Cypher te Neo4j Query API me HTTPS (porti 443) dhe e kthen rezultatin në të njëjtin format si Bolt.",
    "kontrollo_lidhjen": "Ekzekuton `RETURN 1` për të provuar lidhjen; kthen mënyrën që u përdor ('bolt' ose 'https').",
    "_aftesite": "Pyet Ollama-n (/api/show) çfarë di modeli: 'completion', 'thinking', 'vision'...",
    "_fjalori": "Lexon data/fjalori_shqip.json një herë dhe përgatit regex-et (fjalët më të gjata provohen të parat).",
    "_fjalori_en": "Lexon data/fjalori_anglisht.json dhe ndërton listat e fjalëve angleze/shqipe për zbulimin e gjuhës.",
    "_cache": "Lexon cache-in e përkthimeve (data/perkthime_en.json) një herë.",
    "_ruaj": "Ruan cache-in e përkthimeve në disk (me kyç, që dy thirrje të mos përplasen).",
    "_numrat": "Nxjerr të gjithë numrat e tekstit (39,5 dhe 39.5 trajtohen njësoj).",
    "_thirr_modelin": "Thërret gemma3:4b me promptin e përkthimit dhe, nëse jepen, me fjalorin e termave të kësaj përgjigjeje.",
    "kontrollo_urgjencen": "Kontrollon mesazhin (origjinal, standard dhe anglisht→shqip) me regex-et e urgjencës dhe vetëdëmtimit. Kthen mesazhin fiks (shqip ose anglisht) ose None.",
    "Profili": "Mosha, gjendjet (shtatzëni, ulçerë...) dhe shënimet e personit. te_gjitha_gjendjet() shton gjendjet e moshës (nen_12, mbi_65...).",
    "Pergjigje": "Rezultati i pergjigju(): teksti, simptomat, ilaçet, të përjashtuarat, burimet, hapat e mendimit, gjuha, koha.",
    "_pastro": "Heq shenjat e pikësimit (përveç apostrofit).",
    "qellimi_bisedes": "Njeh mesazhet e shkurtra pa ankesë: përshëndetje, faleminderit, mirupafshim, kush je, si je, ok.",
    "qellimi_vijues": "Njeh pyetjet vijuese: doza, këshilla, alternativa, mjeku, info.",
    "_rrenjet": "Rrënjët 4-shkronjëshe të fjalëve kuptimplote (për kontrollin 'fjalë e përbashkët').",
    "gjej_simptomat": "Shkurtim: vetëm simptomat e zgjedhura nga kerko_simptomat().",
    "merr_simptomat_sipas_id": "Lexon simptomat nga grafi sipas id-ve, me të njëjtën renditje.",
    "merr_barnat": "Cypher: ilaçet e simptomave sipas rendit, duke i ndarë në të lejuara dhe të përjashtuara për gjendjet e profilit (KUNDERINDIKOHET_PER); shton kujdeset (KUJDES_ME).",
    "_ka_indeks_pdf": "A ekziston indeksi vektorial i pjesëve (chunk_embedding).",
    "kerko_ne_pdf": "Kërkim vektorial në pjesët (:Chunk): PDF, MedlinePlus, openFDA. Kthen ato mbi pragun 0,60.",
    "_konteksti": "Ndërton tekstin e kontekstit për modelin: profili, simptomat, shenjat e alarmit, ilaçet e lejuara/përjashtuara, burimet.",
    "_lista": "'a, b ose c' nga një listë.",
    "_emrat": "'dhimbje koke dhe kollë e thatë' nga lista e simptomave.",
    "pergjigje_standarde": "Përgjigjja kryesore nga databaza: hyrja, info, ilaçet me kujdeset, të përjashtuarat, këshillat, shenjat e alarmit.",
    "_te_gjitha_barnat": "Të gjitha ilaçet me pattern-in e emrave (gjenerik + tregtar) për t'i njohur kur përmenden.",
    "gjej_barnat_e_permendura": "Gjen ilaçet që përmend mesazhi ('çfarë është ibuprofeni?').",
    "_barnat_sipas_id": "Ilaçet sipas id-ve (nga cache).",
    "pergjigje_per_ilacin": "Karta tekstuale e një ilaçi: për çfarë përdoret, doza, maksimumi, kohëzgjatja; ose pse nuk rekomandohet për profilin.",
    "_shenim_profili": "'ℹ️ E mora parasysh: shtatzëni' kur mesazhi solli gjendje/moshë të re.",
    "_vijuese_doza": "Përgjigjja për 'sa herë ta marr?': dozat e ilaçeve të fundit nga databaza.",
    "_vijuese_alternativa": "Ilaçe të tjera për të njëjtat simptoma, të filtruara për profilin.",
    "_vijuese_keshilla": "Këshillat pa ilaç për simptomat e bisedës.",
    "_vijuese_mjeku": "Shenjat e alarmit: kur duhet mjeku.",
    "_vijuese_info": "Përshkrimi i simptomës (çfarë është, nga vjen).",
    "_numri_frazave": "Numri i frazave në graf (për hapin 'Po kërkoj...').",
    "_lexo_json": "Nxjerr objektin JSON nga përgjigjja e modelit, edhe nëse ka tekst rreth tij.",
    "_pyetje_kandidatesh": "Pyetja 'Cila nga këto?' me listë të numëruar.",
    "_terma": "Lexon data/terma_en.json (emrat anglisht të simptomave, shkruar me dorë).",
    "_burimet_e_ilaceve": "Pjesët e sigurisë (do not use, ask a doctor...) nga fletëudhëzuesit openFDA të ilaçeve.",
    "_emrat_e_gjendjeve": "Emrat shqip të gjendjeve sipas id.",
    "_tekst_i_gjetjeve": "Paragrafi '📄 Kontroll në fletëudhëzuesin zyrtar' në gjuhën e personit.",
    "krijo_skemen": "Krijon kufizimet (id unike) dhe indekset që nevojiten, nëse mungojnë.",
    "shto_person": "Krijon (:Person) me moshë, gjendje dhe shënime. Kthen id-në.",
    "perditeso_person": "Ndryshon emrin, moshën, gjendjet ose shënimet e personit.",
    "lista_personave": "Të gjithë personat me numrin e mesazheve.",
    "merr_person": "Personi me gjendjet e tij, ose None.",
    "ruaj_mesazh": "Ruan (:Mesazh) me lidhjet PER_SIMPTOMEN dhe SUGJEROI.",
    "historia": "Mesazhet e fundit të personit (për të rishfaqur bisedën).",
    "_hash": "PBKDF2-HMAC-SHA256 me kripë, 200 000 iteracione.",
    "ekziston": "A ka llogari me këtë emër përdoruesi.",
    "ndrysho_fjalekalimin": "Ruan hash-in e ri me kripë të re.",
    "ndrysho_rolin": "Ndryshon rolin: 'admin' ose 'perdorues'.",
    "roli_i": "Roli i llogarisë ose None.",
    "numri_adminave": "Sa llogari admin ka (për të mos fshirë adminin e fundit).",
    "lista_llogarive": "Të gjitha llogaritë me rolin dhe datat.",
    "_kohe_ne_tekst": "Data/ora e Neo4j → tekst ISO.",
    "_literal": "Një vlerë si literal Cypher (për skriptin e backup-it).",
    "_harta": "Vetitë e nyjes si hartë Cypher {k: v}.",
    "ne_cypher": "Skripti .cypher që e rikrijon gjithë databazën.",
    "ruaj_backup": "Krijon Desktop\\FarmaBot_Backup\\<data_ora>\\ me databaza.json dhe databaza.cypher.",
    "ka_lokal": "A janë vendosur NEO4J_LOCAL_* te .env.",
    "ngarko": "Ngarkon nyjet dhe lidhjet; për çdo frazë llogarit embedding me bge-m3 (edhe variantin standard).",
    "main": "Pika e nisjes kur skedari ekzekutohet nga terminali.",
    "shkarko_medlineplus": "Gjen skedarin XML më të ri te medlineplus.gov/xml.html dhe e ruan te data/burime/.",
    "shkarko_openfda": "Për çdo ilaç të bazës merr fletëudhëzuesin më të plotë nga api.fda.gov dhe ruan seksionet.",
    "_pa_html": "Heq etiketat HTML nga përmbledhjet e MedlinePlus.",
    "pjeset_medlineplus": "Temat angleze të MedlinePlus të ndara në pjesë ~900 karaktere.",
    "pjeset_openfda": "Seksionet e fletëudhëzuesve openFDA të ndara në pjesë, të lidhura me ilaçin.",
    "_kontrollo_regex": "Kontrollon që fjalët kyçe kompilohen dhe kapin frazat e simptomës.",
    "pergatit_databazen": "Krijon skemën dhe llogarinë admin herën e parë.",
    "_hero": "HTML i faqes së hyrjes (logo + tri vetitë).",
    "faqja_hyrjes": "Hyrja, regjistrimi ose vazhdimi si vizitor.",
    "permbledhje": "📊 Përmbledhje: numrat e databazës dhe ilaçet më të sugjeruara.",
    "perdoruesit_faqe": "👥 Përdoruesit: rolet, fshirja e llogarive.",
    "barnat_faqe": "💊 Ilaçet: redaktimi i ilaçeve dhe shtimi i një ilaçi të ri (ruhet në Neo4j dhe JSON).",
    "backup_faqe": "💾 Backup: krijimi i backup-it dhe kopjimi në Neo4j lokal.",
    "_avatar": "Ikona e mesazhit (FarmaBot ose personi).",
    "_kohezgjatja": "'48 sekonda' / '1 min 12 s' në gjuhën e personit.",
    "_titulli_mendimit": "'🧠 Mendoi për …' ose '🧠 Thought for …'.",
    "faqja": "Vizatimi i faqes (paneli, bisedat, fusha e mesazhit).",
    "gjendjet_nga_db": "Gjendjet nga grafi për checkbox-et e panelit (cache 1 orë).",
    "apliko_ne_pritje": "Zbaton vlerat e vendosura me vendos_me_vone().",
    "_emri_burimit": "Emri i burimit për shënimin 'Burime:'.",
    "shfaq_kartat": "Kartat HTML: ilaçet, të përjashtuarat, shenjat e alarmit, fletëudhëzuesit zyrtarë dhe lidhjet e burimeve.",
    "apliko": "Shton CSS-në e FarmaBot-it në faqe.",
    "_e": "Escape HTML (teksti nga databaza nuk ekzekutohet kurrë si HTML).",
    "karta_ilaci": "Karta e një ilaçi: emrat tregtarë, doza, maksimumi, kohëzgjatja, kujdeset, paralajmërimet.",
    "karta_perjashtuara": "Karta '🚫 Nuk sugjerohen për ty' me arsyet.",
    "karta_alarmi": "Karta '🩺 Kur duhet të shkosh te mjeku'.",
    "_ngarko_profilin": "Mbush panelin dhe bisedën nga databaza (një herë për sesion).",
}


def tabela_e_funksioneve(skedari: str):
    rreshta = []
    for f in funksionet(skedari):
        pershkrimi = PERSHKRIME.get(f["emri"]) if f["emri"] in PERSHKRIME and not f["doc"] else None
        if not pershkrimi:
            pershkrimi = " ".join(f["doc"].split("\n\n")[0].split()) if f["doc"] else PERSHKRIME.get(f["emri"], "–")
        if len(pershkrimi) > 260:
            pershkrimi = pershkrimi[:257] + "…"
        rreshta.append([f["emri"], pershkrimi, f["merr"], f["kthen"]])
    tabele(["Funksioni", "Çfarë bën", "Merr", "Kthen"], rreshta, [3.6, 6.6, 4.0, 2.4], size=8.5, kod_kolona=(0, 2, 3))


# ================================================================ FAQJA E TITULLIT
for _ in range(5):
    doc.add_paragraph()
p("FarmaBot", stil="Title")
p("Dokumentimi i plotë teknik", size=18, ngjyra=GRI)
p("Asistent farmacie në shqip dhe anglisht · GraphRAG lokal me Neo4j dhe Ollama · ndërfaqe web", size=13, ngjyra=GRI)
doc.add_paragraph()
p("Si lidhet me databazën, si funksionon çdo skedar dhe çdo funksion kryesor, me shembuj kodi dhe "
  "shembuj realë bisede. I shkruar për ta mësuar sistemin hap pas hapi.", size=12)
doc.add_paragraph()
p(f"Versioni: {date.today().strftime('%d.%m.%Y')}", size=11, ngjyra=GRI)
p("FarmaBot jep informacion të përgjithshëm; nuk zëvendëson farmacistin ose mjekun.", size=10, ngjyra=GRI,
  italic=True)
faqe_e_re()

p("Përmbajtja", size=20, ngjyra=TEAL).runs[0].font.name = "Cambria"
fushe(doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')
faqe_e_re()

# fundi i faqes: numri i faqes
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run("FarmaBot · Dokumentimi · faqja ")
r.font.size, r.font.color.rgb = Pt(9), GRI
fushe(fp, "PAGE")

# ================================================================ 1. HYRJE
rinis_numrat(); doc.add_heading("1. Çfarë është FarmaBot", 1)
p("FarmaBot është një chatbot farmacie në shqip. Personi shkruan simptomat me fjalët e veta (p.sh. *“më dhemb "
  "dhëmbi”*, *“po m dhem kryt”* ose *“I have a sore throat”*) dhe bota:".replace("*", ""))
for t in ["e kupton mesazhin, edhe në gegërisht, pa ë/ç ose në anglisht;",
          "gjen simptomat në një graf njohurish (Neo4j) me kërkim vektorial dhe fjalë kyçe;",
          "sugjeron ilaçe pa recetë, duke hequr ato që nuk janë të sigurta për moshën dhe gjendjet e personit;",
          "tregon dozat nga databaza, këshillat dhe kur duhet mjeku;",
          "në urgjencë (dhimbje gjoksi, vështirësi në frymëmarrje...) ndalon dhe thotë **127 / 112**."]:
    pika(t)
p("Gjithçka punon lokalisht në kompjuter: databaza Neo4j, modelet gjuhësore (Ollama) dhe ndërfaqja web "
  "(FarmaBot Web, në stilin e ChatGPT / Claude). Asnjë e dhënë shëndetësore nuk dërgohet jashtë. I vetmi shërbim "
  "i jashtëm është Gmail-i, vetëm për email-et e rivendosjes së fjalëkalimit.")
shenim("**Parimi kryesor:** vendimet që mund të dëmtojnë (urgjencat, cilat ilaçe lejohen, dozat) i marrin rregullat "
       "dhe databaza. Modeli gjuhësor ndihmon të kuptohet mesazhi dhe të shkruhet përgjigjja, por nuk zgjedh ilaçe "
       "dhe nuk shkruan doza.")

rinis_numrat(); doc.add_heading("1.1 Si ta lexosh këtë dokument", 2)
for t in ["Kapitulli 2: arkitektura, për pamjen e përgjithshme.",
          "Kapitulli 3: lidhja me databazën, hap pas hapi (.env, config.py, bolt/https/auto, lokal/Aura, backup).",
          "Kapitulli 4: struktura e grafit dhe query-t Cypher.",
          "Kapitujt 5–9: si përpunohet një mesazh: rrjedha, fjalori shqip, anglishtja, mendimi i thellë, datasetet.",
          "Kapitulli 10: siguria. Kapitulli 11: llogaritë, email-i dhe rivendosja e fjalëkalimit.",
          "Kapitulli 12: ndërfaqja web (pamjet, tema, gjuha, bisedat, API).",
          "Kapitulli 13: çdo skedar dhe çdo funksion (çfarë bën, çfarë merr, çfarë kthen).",
          "Kapitulli 14: shembuj realë bisede. Kapitujt 15–17: testet, nisja dhe problemet e shpeshta.",
          "Kapitulli 18: historiku i ndryshimeve (çfarë u shtua në çdo version)."]:
    pika(t)

# ================================================================ 2. ARKITEKTURA
rinis_numrat(); doc.add_heading("2. Arkitektura", 1)
figure("slajdi_03.png", "Figura 1. Pjesët e sistemit dhe si komunikojnë")
tabele(["Pjesa", "Roli", "Ku ndodhet"], [
    ["FarmaBot Web", "Ndërfaqja: hyrja, bisedat, cilësimet, paneli i adminit (HTML/CSS/JS pa librari)", "web/static/"],
    ["Serveri (API)", "Starlette + Uvicorn: sesionet, llogaritë, bisedat, përgjigjet live", "web/server.py, web/admin.py"],
    ["bisedat.py", "Bisedat e ruajtura (shumë për çdo përdorues) me kartat dhe kontekstin", "bisedat.py"],
    ["emaili.py", "Email-et e rivendosjes së fjalëkalimit (SMTP, Gmail)", "emaili.py, .env"],
    ["chatbot.py", "Logjika: urgjenca, profili, kërkimi, filtrimi, përgjigjja, mendimi", "chatbot.py"],
    ["gjuha.py", "Shqipja e folur → standard; zbulimi i anglishtes; anglisht → shqip", "gjuha.py, data/fjalori_*.json"],
    ["perkthimi.py", "Përkthimi i përgjigjes në anglisht me kontroll numrash", "perkthimi.py"],
    ["Neo4j", "Graf: ilaçe, simptoma, gjendje, persona, mesazhe; indekse vektoriale", "neo4j_local\\ (porti 7687)"],
    ["Ollama", "bge-m3 (embeddings), qwen3:8b (mendimi), gemma3:4b (përkthimi, pyetjet e lira)", "porti 11434"],
    ["Të dhënat", "Baza e njohurive, fjalorët, datasetet e shkarkuara", "data/"],
], [3.0, 8.6, 5.0], kod_kolona=(0,))
p("Teknologjitë: Python 3.12, Starlette + Uvicorn (serveri web), HTML/CSS/JavaScript pa librari të jashtme, "
  "Neo4j 2026 (Community, lokal), drajveri zyrtar `neo4j` për Python, "
  "`requests` për Ollama dhe Query API, `python-dotenv` për .env, `pytest` për testet.")

# ================================================================ 3. LIDHJA ME DATABAZËN
rinis_numrat(); doc.add_heading("3. Lidhja me databazën, hap pas hapi", 1)
figure("slajdi_04.png", "Figura 2. Nga .env te query(): një funksion i vetëm për gjithë kodin")

rinis_numrat(); doc.add_heading("3.1 Hapi 1: skedari .env", 2)
p("Kredencialet nuk shkruhen kurrë në kod. Ato janë te skedari `.env` në rrënjën e projektit, i cili është te "
  "`.gitignore` dhe nuk duhet ndarë me askënd. Variablat që përdor sistemi:")
tabele(["Variabli", "Çfarë është", "Shembull"], [
    ["NEO4J_URI", "Adresa e databazës aktive", "bolt://127.0.0.1:7687"],
    ["NEO4J_USERNAME", "Përdoruesi i Neo4j", "neo4j"],
    ["NEO4J_PASSWORD", "Fjalëkalimi i Neo4j", "(sekret)"],
    ["NEO4J_DATABASE", "Emri i databazës (bosh = parazgjedhja)", "neo4j"],
    ["NEO4J_TRANSPORT", "Mënyra e lidhjes: auto, bolt ose https", "bolt"],
    ["NEO4J_AURA_*", "Kredencialet e kopjes në cloud (Aura)", "neo4j+s://xxxx.databases.neo4j.io"],
    ["NEO4J_LOCAL_*", "Databaza lokale për kopjimin Aura → Desktop (opsionale)", "neo4j://127.0.0.1:7687"],
    ["OLLAMA_URL", "Adresa e Ollama-s", "http://127.0.0.1:11434"],
    ["OLLAMA_LLM_MODEL", "Modeli për pyetjet e lira dhe përkthimin", "gemma3:4b"],
    ["OLLAMA_EMBED_MODEL", "Modeli i embeddings", "bge-m3"],
    ["OLLAMA_THINK_MODEL", "Modeli i mendimit të thellë", "qwen3:8b"],
    ["ADMIN_USERNAME / ADMIN_PASSWORD", "Llogaria admin e krijuar herën e parë", "admin / (sekret)"],
], [4.6, 6.6, 5.4], kod_kolona=(0, 2))
kod("""# .env (shembull, me vlera të rreme)
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=fjalekalimi-yt
NEO4J_TRANSPORT=bolt
OLLAMA_LLM_MODEL=gemma3:4b
OLLAMA_EMBED_MODEL=bge-m3""")
shenim("**Kujdes:** `127.0.0.1` dhe jo `localhost`. Në Windows, `localhost` provon fillimisht IPv6 dhe humb rreth 2 "
       "sekonda në çdo lidhje.", "kujdes")

rinis_numrat(); doc.add_heading("3.2 Hapi 2: config.py lexon .env", 2)
p("Në fillim të `config.py`, `load_dotenv()` i fut vlerat e `.env` te variablat e mjedisit. Pastaj çdo pjesë e "
  "kodit i lexon me `os.getenv()`:")
kod("\n".join(burimi("config.py").splitlines()[:21]))

rinis_numrat(); doc.add_heading("3.3 Hapi 3: tri mënyrat e lidhjes (bolt, https, auto)", 2)
tabele(["Mënyra", "Si lidhet", "Kur përdoret"], [
    ["bolt", "Drajveri zyrtar neo4j, protokolli Bolt, porti 7687", "Gjithmonë kur porti 7687 është i hapur (lokal: po). Më i shpejti."],
    ["https", "Neo4j Query API (POST /db/<db>/query/v2) mbi HTTPS, porti 443", "Kur rrjeti (p.sh. universiteti) bllokon portin 7687 te Aura."],
    ["auto", "Provon Bolt-in për 10 sekonda; nëse dështon, kalon vetë në HTTPS", "Parazgjedhja kur NEO4J_TRANSPORT mungon."],
], [2.2, 7.0, 7.4], kod_kolona=(0,))
p("Vendimi merret **një herë për proces** nga `menyra_lidhjes()` (me `lru_cache`). Prova e Bolt-it bëhet në një "
  "thread me afat kohor, sepse drajveri mund të presë shumë gjatë kur porti bllokohet:")
kod(funksioni("config.py", "_bolt_punon") + "\n\n\n" + funksioni("config.py", "menyra_lidhjes"))

rinis_numrat(); doc.add_heading("3.4 Hapi 4: query(), funksioni që përdor gjithë kodi", 2)
p("I gjithë kodi (chatbot.py, perdoruesit.py, bisedat.py, llogarite.py, backup.py, web/) thërret vetëm `query()`. "
  "Ai kthen gjithmonë një listë me dict, njësoj për Bolt dhe HTTPS, kështu që pjesa tjetër e kodit nuk e di "
  "si është lidhur:")
kod(funksioni("config.py", "query"))
p("Parametrat kalojnë gjithmonë si `$emër` te Cypher-i, kurrë të ngjitur te teksti. Kjo mbron nga injektimi "
  "dhe lejon Neo4j të ripërdorë planin e query-t:")
kod("""from config import query

# Merr ilaçet e dhimbjes së kokës
rows = query(
    "MATCH (s:Simptome {id: $id})-[t:TRAJTOHET_ME]->(b:Barna) "
    "RETURN b.emer AS emer ORDER BY t.rendi",
    id="dhimbje_koke",
)
print([r["emer"] for r in rows])
# ['Paracetamol 500 mg', 'Ibuprofen 200/400 mg', 'Naproksen 220 mg', 'Aspirinë 500 mg']""")
p("Për HTTPS, `_query_https()` dërgon të njëjtin Cypher te Query API dhe e kthen përgjigjen (fields + values) në "
  "të njëjtin format:")
kod(funksioni("config.py", "_query_https"))

rinis_numrat(); doc.add_heading("3.5 Hapi 5: provo lidhjen", 2)
kod("""venv_chatbot\\Scripts\\python -c "from config import kontrollo_lidhjen; print(kontrollo_lidhjen())"
# bolt          ← lidhja punon dhe po përdor Bolt""")
p("Nëse del gabim: kontrollo që Neo4j është ndezur (porti 7687), që fjalëkalimi te .env është i saktë, dhe "
  "shiko `logs\\neo4j.err.log`. Shiko edhe kapitullin 16.")

rinis_numrat(); doc.add_heading("3.6 Neo4j lokal (databaza aktive)", 2)
p("Databaza kryesore është Neo4j Community 2026 brenda dosjes `neo4j_local\\`, me Java-n e vet (`neo4j_local\\jre`). "
  "Dëgjon vetëm në `127.0.0.1`, pra nuk arrihet nga kompjuterë të tjerë.")
for t in ["Nisja: `nis_farmabot.ps1` (ose ikona FarmaBot) e nis me `neo4j.bat console` dhe pret portin 7687.",
          "Neo4j Browser: http://localhost:7474 (përdoruesi `neo4j`, fjalëkalimi `NEO4J_PASSWORD`).",
          "Neo4j Desktop: Connect → Remote connection → `bolt://127.0.0.1:7687`.",
          "Të dhënat u kopjuan nga Aura më 19.11.2026; kredencialet e Aura-s ruhen si `NEO4J_AURA_*`."]:
    pika(t)

rinis_numrat(); doc.add_heading("3.7 Neo4j Aura (cloud)", 2)
p("Aura është kopja në cloud. Për të kaluar përsëri në Aura, vendos te .env `NEO4J_URI` = vlera e `NEO4J_AURA_URI` "
  "(dhe përdoruesin/fjalëkalimin përkatës) dhe `NEO4J_TRANSPORT=auto`. Aura Free pauzohet pas disa ditësh pa "
  "përdorim; rinise te console.neo4j.io.")

rinis_numrat(); doc.add_heading("3.8 Krijimi i skemës dhe ngarkimi i të dhënave", 2)
p("Databaza bosh mbushet me dy skripte:")
kod("""python ngarko_grafin.py      # njohuritë: ilaçe, simptoma, gjendje, fraza + embeddings
python ngarko_burimet.py     # datasetet: MedlinePlus + openFDA (pas shkarko_datasetet.py)""")
p("`ngarko_grafin.py` krijon kufizimet e unicitetit dhe indeksin vektorial të frazave:")
kod(funksioni("ngarko_grafin.py", "krijo_skemen"))
p("Pastaj për çdo simptomë krijon nyjen, lidhjet me ilaçet (me rend) dhe frazat me embedding. "
  "Çdo frazë ruhet dy herë: siç është (e normalizuar) dhe në shqip standard (gjuha.py).")

rinis_numrat(); doc.add_heading("3.9 Backup dhe rikthimi", 2)
for t in ["`python backup.py` (ose 💾 Backup te paneli admin) krijon `Desktop\\FarmaBot_Backup\\<data_ora>\\` me "
          "`databaza.json` (të gjitha nyjet dhe lidhjet) dhe `databaza.cypher`.",
          "`databaza.cypher` e rikrijon databazën në çdo Neo4j: hape te Neo4j Browser ose ekzekutoje me cypher-shell.",
          "`python backup.py --lokal` kopjon databazën aktive në një Neo4j Desktop lokal (kërkon `NEO4J_LOCAL_*`).",
          "Embeddings nuk humbin: ruhen si lista numrash dhe vendosen përsëri me db.create.setNodeVectorProperty."]:
    pika(t)

# ================================================================ 4. GRAFI
rinis_numrat(); doc.add_heading("4. Struktura e grafit", 1)
figure("slajdi_05.png", "Figura 3. Nyjet dhe lidhjet")
tabele(["Nyja", "Vetitë kryesore", "Sasia"], [
    ["Barna (ilaçi)", "id, emer, lende_aktive, forma, emra_tregtare, doza, doza_maks, kohezgjatja, si_merret, paralajmerime", "74"],
    ["Simptome", "id, emer, pershkrim, info, shenja_alarmi, keshilla, fjale_kyce, kerkon_mjek", "63"],
    ["Gjendje", "id, emer (shtatzëni, ulçerë, veshka, antikoagulante...)", "25"],
    ["Fraze", "tekst, embedding (1024 numra, bge-m3)", "1 213"],
    ["Chunk", "tekst, burimi, seksioni, url, lloji (medlineplus/openfda/pdf), embedding", "3 558"],
    ["Person, Mesazh, Llogari", "profili, historia, llogaritë e hyrjes", "sipas përdorimit"],
], [3.4, 10.4, 2.8], kod_kolona=(0,))
tabele(["Lidhja", "Kuptimi"], [
    ["(Fraze)-[:I_PERKET]->(Simptome)", "Një mënyrë si e thonë njerëzit simptomën"],
    ["(Simptome)-[:TRAJTOHET_ME {rendi}]->(Barna)", "Ilaçi për simptomën; rendi 0 = zgjedhja e parë"],
    ["(Barna)-[:KUNDERINDIKOHET_PER {arsye}]->(Gjendje)", "Nuk lejohet për këtë gjendje (hiqet nga lista)"],
    ["(Barna)-[:KUJDES_ME {arsye}]->(Gjendje)", "Lejohet, por me paralajmërim"],
    ["(Chunk)-[:PERSHKRUAN]->(Barna)", "Pjesë fletëudhëzuesi (openFDA/PDF) për ilaçin"],
    ["(Person)-[:KA_GJENDJE]->(Gjendje)", "Gjendjet e profilit"],
    ["(Person)-[:DERGOI]->(Mesazh)", "Historia e bisedës"],
    ["(Mesazh)-[:PER_SIMPTOMEN]->(Simptome) / -[:SUGJEROI]->(Barna)", "Për çfarë foli mesazhi dhe çfarë sugjeroi"],
    ["(Llogari)-[:ESHTE]->(Person)", "Llogaria e hyrjes dhe profili i saj"],
], [8.2, 8.4], kod_kolona=(0,))
rinis_numrat(); doc.add_heading("4.1 Filtrimi i ilaçeve në Cypher", 2)
p("Kjo është zemra e sigurisë: ilaçet e kundërindikuara për gjendjet e personit ndahen në Cypher, para se t'i shohë "
  "kushdo tjetër. Funksioni `merr_barnat()`:")
kod(funksioni("chatbot.py", "merr_barnat"))
rinis_numrat(); doc.add_heading("4.2 Query të dobishme për ta eksploruar grafin", 2)
kod("""// Ilaçet e dhimbjes së kokës dhe për kë nuk lejohen
MATCH (s:Simptome {id:'dhimbje_koke'})-[t:TRAJTOHET_ME]->(b:Barna)
OPTIONAL MATCH (b)-[k:KUNDERINDIKOHET_PER]->(g:Gjendje)
RETURN t.rendi, b.emer, collect(g.emer) AS jo_per ORDER BY t.rendi;

// Cilat simptoma kanë më pak fraza (ku duhen shtuar)
MATCH (f:Fraze)-[:I_PERKET]->(s:Simptome)
RETURN s.emer, count(f) AS fraza ORDER BY fraza LIMIT 10;

// Kërkim vektorial i drejtpërdrejtë (në Neo4j Browser, me një vektor nga bge-m3)
CALL db.index.vector.queryNodes('fraze_embedding', 5, $vektori) YIELD node, score
RETURN node.tekst, score;""")

# ================================================================ 5. RRJEDHA
rinis_numrat(); doc.add_heading("5. Rrjedha e një mesazhi", 1)
figure("slajdi_06.png", "Figura 4. Hapat që kalon çdo mesazh")
p("Funksioni kryesor është `pergjigju()` te chatbot.py. Ai merr mesazhin, historinë, profilin dhe kontekstin e "
  "bisedës, dhe kthen një objekt `Pergjigje`. Hapat, me radhë:")
for t in ["**Gjuha.** `gjuha_e_bisedes()` vendos shqip ose anglisht (mesazhet neutrale si “ok” vazhdojnë gjuhën e mëparshme).",
          "**Urgjenca.** `kontrollo_urgjencen()` me regex mbi mesazhin origjinal, variantin standard dhe atë anglisht→shqip. "
          "Nëse ka shenjë urgjence, kthen menjëherë tekstin fiks me 127/112.",
          "**Profili nga teksti.** `lexo_profilin_nga_teksti()` gjen “jam shtatzënë”, “djali 5 vjeç”, “marr varfarinë”, "
          "me mohim (“nuk jam shtatzënë”).",
          "**Bisedë e thjeshtë.** Përshëndetje, faleminderit, mirupafshim, “kush je”: përgjigje e shkurtër; konteksti mbetet.",
          "**Përgjigje e pyetjes sqaruese.** Nëse bota kishte pyetur “e thatë apo me gëlbazë?”, “e thatë” ose “2” zgjidh simptomën.",
          "**Ilaç me emër.** “çfarë është ibuprofeni?” → karta e ilaçit nga databaza.",
          "**Simptomë e re.** `kerko_simptomat()`: kërkim hibrid me vektorë (bge-m3) dhe fjalë kyçe, me prag. "
          "Në modalitetin e mendimit, modeli e rilexon mesazhin (kapitulli 8).",
          "**Ilaçet.** `merr_barnat()` filtron në Cypher sipas gjendjeve; `pergjigje_standarde()` shkruan përgjigjen.",
          "**Pyetje vijuese.** doza, alternativa, këshilla, mjeku, info: nga databaza; pyetje e lirë: modeli me kontekstin e databazës.",
          "**Burimet dhe përkthimi** (në modalitetin e mendimit / në anglisht): kontrolli i fletëudhëzuesve, pastaj përkthimi."]:
    numra(t)
rinis_numrat(); doc.add_heading("5.1 Kërkimi hibrid i simptomave", 2)
p("Për çdo variant të mesazhit (origjinali, shqipja standarde, dhe në mendim formulimi i modelit) llogaritet embedding "
  "dhe krahasohet me të gjitha frazat. Për çdo simptomë mbahet varianti më i afërt. Simptoma pranohet vetëm me një "
  "**sinjal të vërtetë**: fjalë kyçe (regex) ose një fjalë kuptimplote e përbashkët me frazën më të afërt, plus "
  "ngjashmëri mbi pragun 0,68. Nëse disa simptoma janë po aq afër, bota pyet në vend që të hamendësojë.")
kod(funksioni("chatbot.py", "kerko_simptomat"))
tabele(["Konstanta", "Vlera", "Kuptimi"], [
    ["PRAGU_SIMPTOMES", "0.68", "Ngjashmëria minimale (cosine) që një simptomë të pranohet"],
    ["DIFERENCA_MAKS", "0.05", "Simptomat e tjera duhet të jenë afër më të mirës"],
    ["BONUS_FJALE_KYCE", "0.12", "Shtohet kur teksti përmend shprehimisht simptomën"],
    ["PRAGU_MBIVENDOSJES", "0.72", "Pa fjalë kyçe, kërkohet ngjashmëri më e lartë"],
    ["MAKS_SIMPTOMA / MAKS_BARNA", "2 / 4", "Sa simptoma dhe ilaçe tregohen njëherësh"],
], [4.8, 2.0, 9.8], kod_kolona=(0, 1))

# ================================================================ 6. FJALORI SHQIP
rinis_numrat(); doc.add_heading("6. Fjalori i shqipes së folur", 1)
figure("slajdi_07.png", "Figura 5. Shembuj nga fjalori")
p("`gjuha.py` + `data/fjalori_shqip.json` e kthejnë mesazhin në shqip standard (pa ë/ç, shkronja të vogla). "
  "Fjalori ka tri pjesë, që zbatohen me radhë:")
tabele(["Pjesa", "Çfarë bën", "Shembull"], [
    ["shprehje_para", "Shkurtimet e chat-it, para fjalëve", "m'dhemb → me dhemb · s'kam → nuk kam · t'i mbetet"],
    ["fjale", "~540 fjalë: gegërisht, chat, gabime, sinonime", "kryt → koka · lukthi → stomaku · zjarrmi → temperature"],
    ["shprehje_pas", "Shprehje të plota pas fjalëve", "me vjell → te vjell · kam sheqer → kam diabet · sa hapa → sa tableta"],
], [3.2, 6.0, 7.4], kod_kolona=(0,))
kod("""from gjuha import standardizo, ndryshimet

standardizo("po m dhem kryt e kom zjarrmi qe prej dje")
# 'po me dhemb koka e kam temperature prej dje'

standardizo("s'po muj me marr frym")
# 'nuk mund te marr fryme'        → kapet si urgjencë

ndryshimet("m djeg lukthi")
# [('m', 'me'), ('lukthi', 'stomaku')]   → shfaqet te hapat e mendimit""")
p("Mesazhi origjinal nuk humbet: `varianta()` kthen të dy, dhe urgjenca, profili dhe kërkimi i kontrollojnë të dy. "
  "Fjalë të reja shtohen te JSON-i; testet (`tests/test_gjuha.py`) kontrollojnë që çelësat janë të normalizuar.")
shenim("Pas ndryshimit të fjalorit ose të frazave, ekzekuto `python ngarko_grafin.py`, që frazat të ruhen edhe në variantin e ri standard.")

# ================================================================ 7. ANGLISHT
rinis_numrat(); doc.add_heading("7. Shqip dhe anglisht", 1)
figure("slajdi_08.png", "Figura 6. Pyetja në anglisht kalon nga e njëjta logjikë")
p("Rregulli: **pyet në shqip → përgjigje në shqip; pyet në anglisht → përgjigje në anglisht.** Logjika e sigurisë "
  "mbetet një (në shqip), kështu që anglishtja nuk ka rregulla më të dobëta.")
for t in ["**Zbulimi:** `gjuha_e_mesazhit()` numëron fjalë angleze dhe shqipe; në dyshim zgjedh shqipen. "
          "Shkronjat ë/ç e bëjnë menjëherë shqip.",
          "**Kuptimi:** `anglisht_ne_shqip()` me `data/fjalori_anglisht.json` (~117 shprehje): "
          "“I have a sore throat since yesterday” → “kam me dhemb fyti prej dje”.",
          "**Urgjencat:** gjithmonë kontrollohen edhe me fjalorin anglisht; teksti i urgjencës në anglisht është fiks (pa model).",
          "**Përgjigjja:** gemma3:4b e përkthen me një fjalor termash të shkruar me dorë (`data/terma_en.json`), "
          "dhe emrat e simptomave vendosen drejt në anglisht para përkthimit.",
          "**Kontrolli i numrave:** `numrat_perputhen()`. Nëse një numër (dozë, orë, 127) mungon te përkthimi, "
          "përkthimi refuzohet dhe shfaqet origjinali shqip me shënim.",
          "**Kartat:** fushat përkthehen në grup (`perkthe_shume`) dhe ruhen te `data/perkthime_en.json`; "
          "fletëudhëzuesi FDA shfaqet në origjinal."]:
    pika(t)
kod(funksioni("perkthimi.py", "numrat_perputhen"))

# ================================================================ 8. MENDIMI
rinis_numrat(); doc.add_heading("8. Mendimi i thellë", 1)
figure("slajdi_09.png", "Figura 7. Hapat e mendimit")
p("Butoni **🧠 Mendo më thellë** në panelin majtas (i ndezur si parazgjedhje) e bën botën të mendojë para se të "
  "përgjigjet, si Claude: hapat shfaqen live dhe në fund mbyllen si “🧠 Mendoi për 48 sekonda”. "
  "Kohëzgjatja në këtë kompjuter (CPU, pa kartë grafike) është ~30 sekonda deri në 2 minuta.")
rinis_numrat(); doc.add_heading("8.1 Hapat", 2)
for t in ["**Lexon mesazhin** me fjalorin (çast).",
          "**Kërkon në bazë** me rregullat dhe vektorët (çast).",
          "**Mendon** me qwen3:8b (thinking): e rishkruan mesazhin në shqip standard dhe liston simptomat (~30–60 s).",
          "**Krahason me bazën:** nëse rregullat gjetën diçka nga fjalët e personit, ajo mbahet; modeli vetëm e "
          "konfirmon. Modeli ndihmon kur rregullat nuk gjejnë asgjë, dhe edhe atëherë simptoma pranohet me të njëjtat pragje.",
          "**Kontrollon ilaçet** për profilin (Cypher).",
          "**Lexon fletëudhëzuesit zyrtarë** (openFDA): kodi kontrollon nëse përmendin gjendjet e personit "
          "(shtatzëni, mëlçi, hollim gjaku...) dhe e thotë në shqip (çast, pa model).",
          "**Përkthen** nëse personi shkruan anglisht (~30 s)."]:
    numra(t)
shenim("**Pa pritje:** urgjencat, përshëndetjet dhe pyetjet vijuese (“sa herë ta marr?”) përgjigjen menjëherë edhe kur "
       "mendimi është i ndezur. Urgjenca nuk pret kurrë modelin.")
rinis_numrat(); doc.add_heading("8.2 Pse “modeli kupton, baza vendos”", 2)
p("Gjatë provave, qwen3:8b ndonjëherë shpiku simptoma (“kafuzë koka” për një kollë të thatë) ose id që nuk ekzistojnë "
  "(“dhimbje_stomaku”). Prandaj modeli nuk zgjedh kurrë drejtpërdrejt: formulimi i tij shtohet si kërkim, dhe kur "
  "rregullat kanë gjetur diçka nga fjalët e personit, ato kanë përparësi.")
kod(funksioni("chatbot.py", "_mendo_per_simptomat"))
rinis_numrat(); doc.add_heading("8.3 Modeli dhe streaming-u", 2)
p("`config.chat_mendo()` thërret Ollama-n me `think: true` dhe `stream: true`. Çdo copë e arsyetimit i kalohet "
  "ndërfaqes (`on_mendim`), që e shfaq live brenda panelit të statusit. Modeli zgjidhet te .env "
  "(`OLLAMA_THINK_MODEL`); nëse nuk ka aftësinë “thinking” (kontrollohet me /api/show), përdoret modeli i zakonshëm.")

# ================================================================ 9. DATASETET
rinis_numrat(); doc.add_heading("9. Datasetet mjekësore", 1)
figure("slajdi_10.png", "Figura 8. Burimet e të dhënave")
tabele(["Burimi", "Çfarë përmban", "Si përdoret"], [
    ["Baza FarmaBot (data/njohurite.json)", "74 ilaçe, 63 simptoma, 25 gjendje, 926 fraza, doza, kundërindikime",
     "Burimi i vetëm i ilaçeve, dozave dhe filtrimit"],
    ["MedlinePlus (NLM, SHBA)", "~1 000 tema shëndetësore në anglisht → 2 983 pjesë", "Lidhje “lexo më shumë” për simptomën; kontekst për pyetjet e lira"],
    ["openFDA Drug Labels", "Fletëudhëzuesit zyrtarë për 53 ilaçe → 575 pjesë", "Kontrolli i gjendjeve të profilit; teksti origjinal te karta"],
    ["PDF (data/pdf/, opsionale)", "Fletëudhëzues që shton vetë farmacisti", "Kontekst për pyetjet e lira"],
], [4.6, 6.0, 6.0])
kod("""python shkarko_datasetet.py     # shkarkon MedlinePlus (30 MB) dhe openFDA te data/burime/
python ngarko_burimet.py        # i ndan në pjesë, llogarit embeddings (~20 min në CPU), i ngarkon si (:Chunk)
python ngarko_burimet.py openfda    # vetëm fletëudhëzuesit, më shpejt""")
shenim("Dozat që sheh personi vijnë **gjithmonë** nga `data/njohurite.json`. Fletëudhëzuesit e FDA-së janë për tregun "
       "amerikan (doza dhe emra mund të ndryshojnë) dhe përdoren vetëm si kontroll shtesë dhe si informacion.", "kujdes")
p("Disa ilaçe të bazës nuk kanë fletëudhëzues amerikan (ambroksol, butilskopolaminë, racekadotril...). Për disa të tjera "
  "fletëudhëzuesi i gjetur është për një produkt të ngjashëm (p.sh. acetilcisteina me recetë). "
  "Lidhjet ilaç → emër gjenerik janë te `EMRAT_OPENFDA` në shkarko_datasetet.py.")

# ================================================================ 10. SIGURIA
rinis_numrat(); doc.add_heading("10. Siguria", 1)
figure("slajdi_11.png", "Figura 9. Gjashtë mbrojtje të pavarura")
tabele(["Mbrojtja", "Ku", "Çfarë garanton"], [
    ["Urgjencat me rregulla", "kontrollo_urgjencen()", "Dhimbje gjoksi, frymëmarrje, anafilaksi, të fikët, insult, gjakderdhje, mbidozë, "
     "foshnjë me temperaturë, vetëdëmtim → 127/112, para çdo modeli, edhe gegërisht/anglisht"],
    ["Filtrim në Cypher", "merr_barnat()", "Ilaçet e kundërindikuara nuk arrijnë te teksti ose te modeli"],
    ["Dozat nga databaza", "kartat (app.js · htmlKartat)", "Doza, maksimumi dhe kohëzgjatja lexohen nga databaza"],
    ["Pa doza nga modeli", "pastro_dozat()", "Rreshtat me doza numerike në tekstin e modelit zëvendësohen me referencë te kartat"],
    ["Kontroll numrash", "perkthimi.numrat_perputhen()", "Përkthimi nuk ndryshon dot një dozë pa u refuzuar"],
    ["Fëmijët", "Profili.femije", "Pa doza për fëmijë nën 12 (varen nga pesha) → farmacisti/pediatri"],
    ["Të dhënat lokale", "Neo4j dhe serveri në 127.0.0.1", "Asgjë nuk del jashtë; fjalëkalime PBKDF2; çdo tekst escape-ohet para se të shfaqet"],
    ["Sesioni", "web/server.py", "Cookie e nënshkruar (SESSION_SECRET te .env), 14 ditë; bisedat e të tjerëve kthejnë 404"],
    ["Rivendosja", "llogarite.krijo_rivendosje()", "Token i rastësishëm, njëpërdorimësh, 30 minuta; ruhet vetëm hash-i; e njëjta përgjigje edhe për email të panjohur"],
], [3.6, 4.4, 8.6], kod_kolona=(1,))
kod(funksioni("chatbot.py", "pastro_dozat"))

# ================================================================ 11. LLOGARITË
rinis_numrat(); doc.add_heading("11. Llogaritë dhe rolet", 1)
figure("slajdi_12.png", "Figura 10. Rolet")
for t in ["**Vizitor** (“Vazhdo pa llogari”): bisedon normalisht; bisedat dhe profili mbahen vetëm në kujtesën e "
          "serverit dhe humbasin kur mbyllet faqja ose rindizet serveri.",
          "**Përdorues:** bisedat ruhen në Neo4j; Cilësimet → Profili shëndetësor, Llogaria (email-i, fjalëkalimi, "
          "fshirja e llogarisë). Gjendjet e shkruara në bisedë (“jam shtatzënë”) i shtohen profilit.",
          "**Admin:** gjithçka + Paneli i administratorit: Përmbledhje · Përdoruesit (rolet, fjalëkalimet, bisedat) · "
          "Ilaçet · Backup. Herën e parë krijohet `admin` me fjalëkalimin te .env (`ADMIN_PASSWORD`); ndryshoje pas "
          "hyrjes së parë.",
          "Fjalëkalimet: PBKDF2-HMAC-SHA256, kripë e rastësishme, 200 000 iteracione, në (:Llogari)-[:ESHTE]->(:Person).",
          "Emri i përdoruesit pranon shkronja shqipe dhe angleze (ç, ë), shifra dhe _ . - (3–30); “Ëndrra” = “ëndrra”."]:
    pika(t)
kod(funksioni("llogarite.py", "hyr"))

rinis_numrat(); doc.add_heading("11.1 Regjistrimi dhe hyrja me email", 2)
figure("ui_regjistrimi.png", "Figura 11. Regjistrimi: emri i përdoruesit, email-i, mosha (opsionale), fjalëkalimi me butonin e syrit", 12.5)
for t in ["Regjistrimi kërkon **emrin e përdoruesit** dhe **email-in** (fusha e emrit/pseudonimit u hoq). Mosha është opsionale.",
          "Email-i normalizohet (shkronja të vogla, pa hapësira) dhe është **unik**: `CREATE CONSTRAINT llogari_email ... IS UNIQUE`.",
          "Hyrja pranon **email-in ose emrin e përdoruesit**. Hapësirat e kopjuara në skaje të fjalëkalimit nuk e prishin hyrjen.",
          "**Butoni i syrit** anash çdo fushe fjalëkalimi e shfaq ose e fsheh tekstin, që personi të kontrollojë çfarë shkroi.",
          "Llogaritë e vjetra pa email e shtojnë te **Cilësimet → Llogaria → Email-i** (kërkohet fjalëkalimi aktual)."]:
    pika(t)

rinis_numrat(); doc.add_heading("11.2 Rivendosja e fjalëkalimit me email", 2)
figure("ui_harrova.png", "Figura 12. “Ke harruar fjalëkalimin?”: personi shkruan email-in e llogarisë", 12.5)
for t in ["Te hyrja, **Ke harruar fjalëkalimin?** → personi shkruan email-in → `POST /api/harrova`.",
          "Nëse email-i ka llogari, krijohet një token i rastësishëm (`secrets.token_urlsafe(32)`). Në Neo4j ruhet vetëm "
          "**hash-i SHA-256** i tij, bashkë me skadimin (30 minuta).",
          "`emaili.py` dërgon me SMTP (Gmail) një email me lidhjen `http://localhost:8501/#/rivendos/<token>`.",
          "Lidhja hap faqen “Zgjidh fjalëkalimin e ri” → `POST /api/rivendos`. Token-i fshihet pas përdorimit: "
          "lidhja vlen **vetëm një herë**.",
          "Përgjigjja është e njëjtë edhe kur email-i nuk ekziston (nuk zbulohet kush ka llogari). Brenda 60 sekondave "
          "nuk dërgohet email i dytë për të njëjtën llogari."]:
    numra(t)
p("Konfigurimi te `.env` (Gmail kërkon Verifikimin me 2 hapa dhe një **App password**, jo fjalëkalimin e zakonshëm):")
kod("""SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=adresa@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx      # App password nga myaccount.google.com/apppasswords
SMTP_FROM=FarmaBot <adresa@gmail.com>
FARMABOT_URL=http://localhost:8501     # adresa që del te lidhja e email-it""")
shenim("Pa SMTP të konfiguruar, email-i nuk dërgohet: shkruhet te `logs/emailet.log`, dhe faqja e thotë këtë. "
       "Lidhja hapet vetëm në kompjuterin ku punon FarmaBot, sepse serveri dëgjon vetëm në `127.0.0.1`.", "kujdes")
kod(funksioni("llogarite.py", "krijo_rivendosje") + "\n\n\n" + funksioni("llogarite.py", "rivendos_fjalekalimin"))

# ================================================================ 12. NDËRFAQJA WEB
rinis_numrat(); doc.add_heading("12. Ndërfaqja web", 1)
p("Ndërfaqja është shkruar nga e para në stilin e ChatGPT / Claude: serveri Python (`web/server.py`, Starlette + "
  "Uvicorn) dhe një faqe e vetme HTML/CSS/JavaScript pa librari të jashtme (`web/static/`). Niset me "
  "`python -m web` dhe hapet te http://localhost:8501.")
figure("ui_bosh.png", "Figura 13. Bisedë e re: përshëndetja, fusha e shkrimit dhe shembujt")
figure("ui_pergjigja.png", "Figura 14. Përgjigjja: hapat (të mbyllshëm), teksti pa emoji dhe kartat e ilaçeve më poshtë")

rinis_numrat(); doc.add_heading("12.1 Pjesët e faqes", 2)
tabele(["Pjesa", "Çfarë bën"], [
    ["Paneli majtas", "Bisedë e re; Paneli i administratorit (vetëm admin); kërkimi; lista e bisedave sipas datës "
     "(Sot, Dje, 7 ditët e fundit, 30 ditët e fundit, Më herët); menuja ⋯: riemërto, shkarko, fshi"],
    ["Butoni i panelit", "E mbyll / hap panelin majtas (edhe me Ctrl+B); gjendja mbahet në shfletues. Në celular paneli del sipër faqes"],
    ["Koka", "Titulli i bisedës, shkarkimi si .md dhe ndërrimi i shpejtë i temës (diell / hënë)"],
    ["Fusha e shkrimit", "Enter dërgon, Shift+Enter rresht i ri; zgjerohet vetë; butoni Mendo më thellë (i fikur si parazgjedhje)"],
    ["Përgjigjja", "Hapat e mendimit (“U përgjigj për 3 sekonda”), teksti, kartat e ilaçeve, ilaçet që s'të përshtaten, "
     "kur duhet mjeku, fletëudhëzuesi FDA, burimet; butoni Kopjo"],
    ["Poshtë majtas", "Emri dhe roli; menuja: Profili shëndetësor, Cilësimet, Paneli i administratorit, Dil"],
], [3.6, 13.0], kod_kolona=())

rinis_numrat(); doc.add_heading("12.2 Tema, gjuha dhe paneli", 2)
figure("ui_cilesimet.png", "Figura 15. Cilësimet në temën e zezë: tema, gjuha, mendimi i thellë, shkurtoret")
for t in ["**Tema:** Sistemi / E bardhë / E zezë. Ngjyrat janë variabla CSS (`:root` dhe `[data-theme=\"dark\"]` "
          "te app.css). Tema vendoset para se të vizatohet faqja, që të mos ketë “flash” të bardhë.",
          "**Gjuha:** Shqip / English ndryshon gjithë ndërfaqen dhe gjuhën e përgjigjeve. Me English, bota përgjigjet "
          "anglisht edhe kur pyetja shkruhet shqip: `pergjigju(..., gjuha=\"en\")`, dhe kartat përkthehen me kontrollin e numrave.",
          "**Ruajtja:** tema, gjuha, mendimi dhe gjendja e panelit ruhen te `localStorage` i shfletuesit.",
          "**Shkurtoret:** Ctrl+Shift+O bisedë e re · Ctrl+B paneli · Enter dërgo · Shift+Enter rresht i ri · Esc mbyll dritaren."]:
    pika(t)
figure("ui_paneli_mbyllur.png", "Figura 16. Paneli majtas i mbyllur në temën e zezë")

rinis_numrat(); doc.add_heading("12.3 Bisedat në databazë", 2)
p("Çdo përdorues ka shumë biseda. Mesazhet ruhen bashkë me kartat (JSON), që biseda të rishfaqet e plotë kur rihapet, "
  "dhe me kontekstin (simptomat, ilaçet, pyetja sqaruese), që biseda të vazhdojë aty ku mbeti:")
kod("""(:Person)-[:KA_BISEDE]->(:Bisede {id, titull, krijuar, perditesuar, konteksti})
(:Bisede)-[:PERMBAN]->(:Mesazh {id, roli, tekst, ora, te_dhena})
(:Person)-[:DERGOI]->(:Mesazh)        // si më parë: statistikat e adminit""")
p("Mesazhet e versionit të vjetër (pa bisedë) mblidhen automatikisht në një bisedë “Biseda e mëparshme”.")

rinis_numrat(); doc.add_heading("12.4 API dhe përgjigjja live", 2)
tabele(["Kërkesa", "Çfarë bën"], [
    ["GET /api/sesioni", "Kush je (llogaria ose vizitor), profili, lista e gjendjeve"],
    ["POST /api/hyr · /api/regjistrohu · /api/vizitor · /api/dil", "Hyrja (email ose emër), regjistrimi (me email), vizitori, dalja"],
    ["POST /api/harrova · /api/rivendos", "Email-i i rivendosjes; fjalëkalimi i ri me token"],
    ["PUT /api/profili · /api/email; POST /api/fjalekalimi; DELETE /api/llogaria", "Profili shëndetësor, email-i, fjalëkalimi, fshirja"],
    ["GET /api/bisedat · /api/bisedat/{id}", "Lista e bisedave; mesazhet e një bisede"],
    ["PATCH · DELETE /api/bisedat/{id}", "Riemërto / fshi bisedën"],
    ["POST /api/biseda", "Mesazh i ri; përgjigjja vjen live si NDJSON: bisede → hap → mendim → fund"],
    ["/api/admin/...", "Përmbledhja, përdoruesit, ilaçet, backup-i (vetëm për rolin admin)"],
], [6.6, 10.0], kod_kolona=(0,))
p("Përgjigjja live: serveri e ekzekuton `pergjigju()` në një thread dhe çdo hap (`on_hap`) dhe copë arsyetimi "
  "(`on_mendim`) i dërgohet menjëherë shfletuesit si një rresht JSON. Në fund vjen `fund` me tekstin e pastruar nga "
  "emoji-t (`web/pergjigja.py`) dhe kartat. Shembull:")
kod("""{"lloji": "bisede", "id": "5a5a…", "titull": "më dhemb koka"}
{"lloji": "hap", "tekst": "Po kërkoj në bazën e njohurive…"}
{"lloji": "fund", "pergjigja": {"tekst": "…", "barnat": [...], "te_perjashtuara": [...], "alarmi": [...]}}""")

# ================================================================ 12. SKEDARËT DHE FUNKSIONET
rinis_numrat(); doc.add_heading("13. Skedarët dhe funksionet", 1)
p("Për çdo skedar: çfarë bën, dhe tabela e funksioneve me parametrat (Merr) dhe vlerën që kthejnë (Kthen). "
  "Funksionet që fillojnë me `_` janë të brendshme (përdoren vetëm brenda skedarit).")
SKEDARET = [
    ("config.py", "Konfigurimi: lidhja me Neo4j (bolt/https/auto), embeddings, modelet e Ollama-s, normalizimi."),
    ("gjuha.py", "Shqipja e folur → standard; zbulimi i anglishtes; anglisht → shqip."),
    ("perkthimi.py", "Përkthimi i përgjigjeve në anglisht me kontroll numrash dhe cache."),
    ("chatbot.py", "Logjika e plotë e bisedës: urgjenca, profili, kërkimi, filtrimi, përgjigjet, mendimi, burimet."),
    ("perdoruesit.py", "Personat (profili shëndetësor) në Neo4j."),
    ("bisedat.py", "Bisedat e ruajtura: lista, mesazhet me kartat, konteksti, riemërtimi, fshirja."),
    ("llogarite.py", "Llogaritë e hyrjes, email-i, fjalëkalimet, rivendosja me token, rolet."),
    ("emaili.py", "Dërgimi i email-eve me SMTP (rivendosja e fjalëkalimit)."),
    ("backup.py", "Backup në Desktop dhe kopjim në Neo4j lokal."),
    ("ngarko_grafin.py", "Ngarkon data/njohurite.json në Neo4j me embeddings."),
    ("ngarko_pdf.py", "Ngarkon fletëudhëzues PDF nga data/pdf/ (opsionale)."),
    ("shkarko_datasetet.py", "Shkarkon MedlinePlus dhe openFDA te data/burime/."),
    ("ngarko_burimet.py", "Ngarkon datasetet si (:Chunk) me embeddings."),
    ("zgjero_njohurite.py", "Zgjerimi 2 i bazës: fraza, fjalë kyçe, ilaçe dhe simptoma të reja."),
    ("zgjero_njohurite_3.py", "Zgjerimi 3: 262 fraza në shqipen e folur."),
    ("web/server.py", "Serveri web: sesionet, llogaritë, profili, bisedat dhe përgjigjet live (NDJSON)."),
    ("web/admin.py", "API e administratorit: përmbledhja, përdoruesit, ilaçet, backup-i."),
    ("web/pergjigja.py", "Përgjigjja e botit → JSON për faqen: teksti pa emoji, kartat, përkthimi i kartave."),
]
for skedari, pershkrim in SKEDARET:
    rinis_numrat(); doc.add_heading(skedari, 3)
    p(pershkrim)
    tabela_e_funksioneve(skedari)
rinis_numrat(); doc.add_heading("Skedarë të tjerë", 3)
tabele(["Skedari", "Çfarë është"], [
    ["data/njohurite.json", "Baza e njohurive: ilaçe, simptoma, gjendje, fraza (burimi i së vërtetës)"],
    ["data/fjalori_shqip.json", "Fjalori i shqipes së folur"],
    ["data/fjalori_anglisht.json", "Anglisht → shqip dhe listat për zbulimin e gjuhës"],
    ["data/terma_en.json", "Emrat anglisht të simptomave dhe termave (me dorë)"],
    ["data/perkthime_en.json", "Cache e përkthimeve (krijohet vetë; mund të rishikohet nga një njeri)"],
    ["data/burime/", "MedlinePlus XML dhe openFDA JSON të shkarkuara"],
    ["nis_farmabot.ps1 / ndal_farmabot.ps1", "Nisja dhe ndalimi i Ollama, Neo4j dhe aplikacionit"],
    ["web/static/index.html", "Faqja e vetme; vendos temën para vizatimit"],
    ["web/static/app.js", "E gjithë ndërfaqja: tekstet SQ/EN, ikonat, hyrja, paneli, biseda, cilësimet, admini"],
    ["web/static/app.css", "Stili dhe dy temat (variabla CSS)"],
    ["web/__main__.py", "python -m web: nis Uvicorn në 127.0.0.1:8501"],
    ["assets/krijo_ikonen.py", "Krijon ikonën dhe logot (logo.png, logo_erret.png, farmabot.ico)"],
    ["testo.py", "Provë e shpejtë nga terminali"],
    ["tests/", "Testet automatike (kapitulli 15)"],
    ["dokumentimi/", "Ky dokument, prezantimi dhe skriptet që i krijojnë"],
], [5.6, 11.0], kod_kolona=(0,))
rinis_numrat(); doc.add_heading("13.1 Shembull: thirrja e botës nga Python", 2)
kod("""from chatbot import Konteksti, Profili, pergjigju

profili = Profili(mosha=34, gjendjet={"ulcer"})
p = pergjigju("po m dhem kryt prej dy ditsh", historia=[], profili=profili,
              konteksti=Konteksti(), mendo=False)

print(p.qellimi)                         # 'simptome'
print([s["id"] for s in p.simptomat])    # ['dhimbje_koke']
print([b["emer"] for b in p.barnat])     # paracetamoli; NSAID-të përjashtohen për ulçerën
print([x["emer"] for x in p.te_perjashtuara])
print(p.tekst)                           # teksti që sheh personi (markdown)""")

# ================================================================ 13. SHEMBUJ BISEDE
rinis_numrat(); doc.add_heading("14. Shembuj realë bisede", 1)
p("Këto biseda u gjeneruan nga bota reale (`dokumentimi/shembuj_bisede.json`). Përgjigjet e gjata janë shkurtuar me “…”; "
  "kartat me doza nuk shfaqen këtu.")


def mesazh_bote(tekst: str, maks=900):
    tekst = tekst.strip()
    if len(tekst) > maks:
        tekst = tekst[:maks].rsplit("\n", 1)[0] + "\n…"
    for rr in tekst.splitlines():
        rr = rr.strip()
        if not rr:
            continue
        rr = rr.replace("_", "")
        par = p(rr[2:] if rr.startswith("- ") else rr, stil="List Bullet 2" if rr.startswith("- ") else None, size=10)
        par.paragraph_format.left_indent = Cm(1.0) if not rr.startswith("- ") else Cm(1.6)
        par.paragraph_format.space_after = Pt(2)


biseda = json.loads((DOK / "shembuj_bisede.json").read_text(encoding="utf-8"))
for b in biseda:
    rinis_numrat(); doc.add_heading(b["emri"], 2)
    for m in b["mesazhet"]:
        par = p(m["personi"], bold_fillim="👤 Personi:  ", ngjyra=None)
        par.paragraph_format.space_before = Pt(8)
        p(f"(qëllimi: {m['qellimi']} · gjuha: {m['gjuha']} · {m['sekonda']} s)", size=8.5, ngjyra=GRI)
        p("", bold_fillim="💊 FarmaBot:", ngjyra=TEAL)
        mesazh_bote(m["bota"])

mendimi = DOK / "shembull_mendimi.json"
if mendimi.exists():
    m = json.loads(mendimi.read_text(encoding="utf-8"))
    rinis_numrat(); doc.add_heading("Mendimi i thellë: hapat e një përgjigjeje", 2)
    p(m["personi"], bold_fillim="👤 Personi:  ")
    p(f"Hapat që u shfaqën (gjithsej {m['sekonda']} sekonda):", ngjyra=GRI, size=10)
    for h in m["hapat"]:
        pika(h)
    p("", bold_fillim="💊 FarmaBot:", ngjyra=TEAL)
    mesazh_bote(m["bota"], maks=3000)

# ================================================================ 14. TESTET
rinis_numrat(); doc.add_heading("15. Testet", 1)
kod("""venv_chatbot\\Scripts\\python -m pytest            # të gjitha (pa model gjuhësor), ~1 minutë
venv_chatbot\\Scripts\\python -m pytest -m llm     # testet me modelin (mendimi, përkthimi), më të ngadalta
venv_chatbot\\Scripts\\python -m pytest tests/test_gjuha.py -q""")
tabele(["Skedari", "Çfarë teston"], [
    ["test_te_dhenat.py", "Integriteti i JSON-it, referencat, kundërindikimet kritike"],
    ["test_urgjenca.py", "Urgjencat dhe vetëdëmtimi kapen; simptomat e lehta jo"],
    ["test_profili.py", "Gjendjet nga teksti, mohimi, mosha, qëllimet e bisedës"],
    ["test_simptomat.py", "~150 mënyra si e shkruajnë njerëzit simptomën; mesazhe pa lidhje"],
    ["test_siguria.py", "Çdo kundërindikim × çdo simptomë (gjenerohet nga të dhënat)"],
    ["test_biseda.py", "Biseda me shumë mesazhe, sqarime, pyetje vijuese"],
    ["test_gjuha.py", "Fjalori: gegërisht/chat → standard, urgjenca dhe profili gegërisht, mendimi (-m llm)"],
    ["test_anglisht.py", "Zbulimi i gjuhës, anglisht → shqip, urgjencat anglisht, kontrolli i numrave, përkthimi (-m llm)"],
    ["test_regjistrimi.py", "Shkronjat shqipe/angleze, hyrja, fjalëkalimi, fshirja"],
    ["test_web.py", "Aplikacioni web: hyrja me email, regjistrimi, rivendosja e fjalëkalimit, bisedat, profili, admini"],
], [4.6, 12.0], kod_kolona=(0,))
p("Testet që kanë nevojë për Neo4j/Ollama anashkalohen vetë kur shërbimet nuk janë ndezur. Testet e web-it përdorin "
  "`TestClient` të Starlette-it dhe nuk dërgojnë email të vërtetë (dërgimi zëvendësohet në test).")

# ================================================================ 15. NISJA
rinis_numrat(); doc.add_heading("16. Nisja e sistemit", 1)
for t in ["Herën e parë: `ollama pull bge-m3`, `ollama pull qwen3:8b`, `ollama pull gemma3:4b`.",
          "Kliko dy herë ikonën **FarmaBot** në Desktop (ose `nis_farmabot.ps1`). Skripti nis me radhë Ollama (11434), "
          "Neo4j lokal (7687, 7474) dhe FarmaBot Web (`python -m web`, 8501), dhe pret që secili port të hapet.",
          "Shfletuesi hapet te http://localhost:8501.",
          "Ndalimi: “Ndal FarmaBot” në dosjen e projektit. Log-et janë te `logs\\`.",
          "Për email-et e rivendosjes: plotëso `SMTP_*` te `.env` (kapitulli 11.2)."]:
    numra(t)
p("Pas ndryshimeve:")
tabele(["Kur ndryshon...", "Ekzekuto"], [
    ["data/njohurite.json ose fjalorin shqip", "python ngarko_grafin.py"],
    ["datasetet (një herë në muaj, sipas dëshirës)", "python shkarko_datasetet.py  →  python ngarko_burimet.py"],
    ["PDF te data/pdf/", "python ngarko_pdf.py"],
    ["kodin Python", "rinis aplikacionin (Ndal FarmaBot → FarmaBot)"],
    ["web/static (HTML/CSS/JS)", "rrit numrin ?v= te index.html; në shfletues Ctrl+F5"],
    ["dokumentimin (pas çdo ndryshimi)", "python dokumentimi/krijo_dokumentimin.py  →  PDF me Word"],
], [7.2, 9.4], kod_kolona=(1,))

# ================================================================ 16. PROBLEMET
rinis_numrat(); doc.add_heading("17. Problemet e shpeshta", 1)
tabele(["Simptoma", "Shkaku i mundshëm", "Zgjidhja"], [
    ["“Ndodhi një gabim… Kontrollo që Ollama dhe Neo4j janë ndezur”", "Një nga shërbimet nuk po punon",
     "Nis FarmaBot nga ikona; shiko logs\\neo4j.err.log dhe logs\\ollama.err.log"],
    ["ServiceUnavailable / connection refused", "Neo4j nuk është ndezur ose porti 7687 është i zënë",
     "netstat -ano | findstr 7687; rinise me nis_farmabot.ps1"],
    ["AuthError", "Fjalëkalimi te .env nuk përputhet", "Kontrollo NEO4J_PASSWORD; provo te http://localhost:7474"],
    ["Aura: lidhja zgjat dhe dështon", "Rrjeti bllokon 7687 ose Aura është në pauzë",
     "NEO4J_TRANSPORT=auto ose https; rinise instancën te console.neo4j.io"],
    ["Mendimi zgjat shumë (> 3 min)", "Modeli në CPU, ose modelet po ngarkohen nga disku",
     "Pyetja e parë pas nisjes është më e ngadalta; fike butonin 🧠 për përgjigje të menjëhershme"],
    ["Përgjigjja anglisht del shqip me shënim", "Përkthimi nuk kaloi kontrollin e numrave", "Kjo është masë sigurie; pyet përsëri ose shkruaj shqip"],
    ["Ndryshimet nuk duken / pamja e vjetër", "Serveri i vjetër është ende ndezur, ose shfletuesi mban cache",
     "Ndal FarmaBot → FarmaBot; në shfletues Ctrl+F5"],
    ["“Email-i, emri ose fjalëkalimi nuk është i saktë”", "Fjalëkalim i gabuar ose llogari pa email",
     "Butoni i syrit për ta kontrolluar; Ke harruar fjalëkalimin?; admini mund të vendosë fjalëkalim të ri"],
    ["Email-i i rivendosjes nuk vjen", "Spam, SMTP i pakonfiguruar ose App password i gabuar",
     "Shiko Spam; kontrollo SMTP_* te .env; pa SMTP lidhja është te logs\\emailet.log"],
    ["Lidhja e email-it nuk hapet në telefon", "Serveri dëgjon vetëm në këtë kompjuter (127.0.0.1)",
     "Hape lidhjen në kompjuterin ku punon FarmaBot"],
    ["Bota nuk e njeh një fjalë", "Mungon te fjalori ose te frazat",
     "Shtoje te data/fjalori_shqip.json ose te frazat e simptomës; pastaj ngarko_grafin.py"],
], [5.0, 5.2, 6.4], kod_kolona=())

# ================================================================ FJALORTH
rinis_numrat(); doc.add_heading("Fjalorth", 1)
tabele(["Termi", "Kuptimi"], [
    ["GraphRAG", "Retrieval-Augmented Generation me graf: përgjigjja ndërtohet nga të dhëna të gjetura në graf"],
    ["Embedding", "Vektor numrash (1024 për bge-m3) që përfaqëson kuptimin e një teksti"],
    ["Ngjashmëria cosine", "Sa afër janë dy vektorë (1 = njësoj); përdoret për të gjetur frazën më të afërt"],
    ["Cypher", "Gjuha e query-ve të Neo4j"],
    ["Bolt", "Protokolli binar i Neo4j (porti 7687)"],
    ["Thinking", "Modeli shkruan arsyetimin para përgjigjes (qwen3)"],
    ["OTC", "Over the counter: ilaç pa recetë"],
    ["Kundërindikim", "Gjendje për të cilën ilaçi nuk duhet përdorur"],
    ["Starlette / Uvicorn", "Framework-u web në Python dhe serveri që e ekzekuton"],
    ["NDJSON", "Një objekt JSON për çdo rresht; lejon që përgjigjja të vijë live, copë pas cope"],
    ["SMTP / App password", "Protokolli i dërgimit të email-eve; fjalëkalim i veçantë që Gmail jep për aplikacione"],
    ["Token", "Kod i rastësishëm njëpërdorimësh te lidhja e rivendosjes"],
], [3.8, 12.8], kod_kolona=())

# ================================================================ 18. HISTORIKU
rinis_numrat(); doc.add_heading("18. Historiku i ndryshimeve", 1)
p("Çdo ndryshim i ri shtohet këtu dhe dokumenti rikrijohet (Word + PDF).")
HISTORIKU = [
    ("22.11.2026", "Llogaritë me email", [
        "Regjistrimi kërkon email; fusha “Emri ose pseudonimi” u hoq.",
        "Hyrja me email ose me emër përdoruesi; hapësirat e kopjuara te fjalëkalimi nuk e prishin hyrjen.",
        "Butoni i syrit te çdo fushë fjalëkalimi.",
        "“Ke harruar fjalëkalimin?”: rivendosja me email (Gmail SMTP, token 30 minuta, njëpërdorimësh).",
        "Email-i shtohet / ndryshohet te Cilësimet → Llogaria; admini i sheh email-et te tabela e përdoruesve."]),
    ("22.11.2026", "FarmaBot Web (zëvendëson Streamlit)", [
        "Aplikacion web në stilin e ChatGPT / Claude: paneli majtas me listën e bisedave, kërkimi, riemërtimi, shkarkimi, fshirja.",
        "Tema Sistemi / E bardhë / E zezë dhe gjuha Shqip / English për gjithë ndërfaqen dhe përgjigjet.",
        "Paneli majtas hapet / mbyllet (edhe me Ctrl+B); cilësimet, profili shëndetësor, llogaria.",
        "Shumë biseda për përdorues në Neo4j (bisedat.py), me kartat dhe kontekstin e secilës.",
        "Paneli i administratorit: përmbledhje, përdoruesit (rolet, fjalëkalimet, bisedat), ilaçet (ndrysho / shto), backup.",
        "Teksti i përgjigjeve pa emoji; ikona të pakta e të njëtrajtshme; “Mendo më thellë” i fikur si parazgjedhje."]),
    ("22.11.2026", "Ikona e re", [
        "Ikona dhe logot e reja (flluskë bisede me kapsulë), edhe logo për temën e zezë; ikona e Desktop-it u përditësua."]),
]
for data, titulli, pikat in HISTORIKU:
    rinis_numrat(); doc.add_heading(f"{data} · {titulli}", 3)
    for t in pikat:
        pika(t)

doc.core_properties.title = "FarmaBot: dokumentimi teknik"
doc.core_properties.author = "FarmaBot"
doc.save(DALJA)
print(f"U ruajt: {DALJA}")
