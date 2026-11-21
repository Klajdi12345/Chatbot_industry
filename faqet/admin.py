"""Paneli i administratorit: përmbledhje, përdoruesit, ilaçet dhe backup-i."""
import json
import os

import streamlit as st

import backup
import chatbot
import llogarite
import perdoruesit as db_p
from config import ROOT, menyra_lidhjes, query
from faqet.perbashket import gjendjet_nga_db, perdoruesi

SKEDARI_NJOHURIVE = ROOT / "data" / "njohurite.json"


# ---------------------------------------------------------------- 📊 Përmbledhje
def permbledhje():
    st.title("📊 Përmbledhje")
    st.caption(f"Databaza: Neo4j Aura · lidhja: **{menyra_lidhjes().upper()}**")
    n = query("""
        CALL () { MATCH (l:Llogari) RETURN count(l) AS llogari }
        CALL () { MATCH (p:Person) RETURN count(p) AS persona }
        CALL () { MATCH (m:Mesazh {roli: 'user'}) RETURN count(m) AS pyetje }
        CALL () { MATCH (b:Barna) RETURN count(b) AS barna }
        CALL () { MATCH (s:Simptome) RETURN count(s) AS simptoma }
        RETURN llogari, persona, pyetje, barna, simptoma""")[0]
    k = st.columns(5)
    for kol, (etiketa, celesi) in zip(k, [("Llogari", "llogari"), ("Persona", "persona"),
                                          ("Pyetje", "pyetje"), ("Ilaçe", "barna"),
                                          ("Simptoma", "simptoma")]):
        kol.metric(etiketa, n[celesi])

    m1, m2 = st.columns(2)
    with m1:
        st.subheader("Simptomat më të shpeshta")
        rows = query("MATCH (:Mesazh)-[:PER_SIMPTOMEN]->(s:Simptome) "
                     "RETURN s.emer AS Simptoma, count(*) AS Herë ORDER BY Herë DESC LIMIT 10")
        st.dataframe(rows, hide_index=True, width="stretch") if rows else st.info("Ende pa të dhëna.")
    with m2:
        st.subheader("Ilaçet më të sugjeruara")
        rows = query("MATCH (:Mesazh)-[:SUGJEROI]->(b:Barna) "
                     "RETURN b.emer AS Ilaçi, count(*) AS Herë ORDER BY Herë DESC LIMIT 10")
        st.dataframe(rows, hide_index=True, width="stretch") if rows else st.info("Ende pa të dhëna.")

    st.subheader("Pyetjet e fundit")
    rows = query("MATCH (p:Person)-[:DERGOI]->(m:Mesazh {roli: 'user'}) "
                 "RETURN substring(toString(m.ora), 0, 16) AS Ora, p.emer AS Personi, m.tekst AS Pyetja "
                 "ORDER BY m.ora DESC LIMIT 15")
    st.dataframe(rows, hide_index=True, width="stretch") if rows else st.info("Ende pa pyetje.")


# ---------------------------------------------------------------- 👥 Përdoruesit
def perdoruesit_faqe():
    st.title("👥 Përdoruesit")
    unë = perdoruesi()["perdoruesi"]
    llogarite_lista = llogarite.lista_llogarive()
    st.dataframe([{"Përdoruesi": l["perdoruesi"], "Roli": l["roli"], "Emri": l["emer"], "Mosha": l["mosha"],
                   "Mesazhe": l["mesazhe"], "Krijuar": (l["krijuar"] or "")[:16].replace("T", " "),
                   "Hyrja e fundit": (l["hyrja_fundit"] or "")[:16].replace("T", " ")}
                  for l in llogarite_lista], hide_index=True, width="stretch")

    with st.expander("➕ Krijo llogari të re"):
        with st.form("llogari_e_re", clear_on_submit=True):
            u = st.text_input("Emri i përdoruesit")
            emer = st.text_input("Emri i plotë (opsional)")
            fj = st.text_input("Fjalëkalimi (min. 8)", type="password")
            roli = st.selectbox("Roli", llogarite.ROLET, format_func=lambda r: "Admin" if r == "admin" else "Përdorues")
            if st.form_submit_button("Krijo"):
                try:
                    llogarite.krijo_llogari(u, fj, roli, emer or None)
                    st.success(f"Llogaria '{u}' u krijua.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    if not llogarite_lista:
        return
    st.subheader("Menaxho një llogari")
    zgjedhur = st.selectbox("Llogaria", [l["perdoruesi"] for l in llogarite_lista])
    l = next(x for x in llogarite_lista if x["perdoruesi"] == zgjedhur)
    t1, t2, t3 = st.tabs(["💬 Bisedat", "⚙️ Roli dhe fjalëkalimi", "🗑️ Fshirja"])
    with t1:
        person = db_p.merr_person(l["person_id"]) if l["person_id"] else None
        if person:
            gj = gjendjet_nga_db()
            st.markdown(f"**Mosha:** {person['mosha'] if person['mosha'] is not None else '–'} · "
                        f"**Gjendje:** {', '.join(gj.get(g, g) for g in person['gjendjet']) or '–'} · "
                        f"**Shënime:** {person['shenime'] or '–'}")
        historia = db_p.historia(l["person_id"], 200) if l["person_id"] else []
        if not historia:
            st.info("Pa biseda.")
        for m in historia:
            with st.chat_message(m["role"]):
                st.caption(m["ora"][:16].replace("T", " "))
                st.markdown(m["content"])
    with t2:
        roli_i_ri = st.radio("Roli", llogarite.ROLET, index=llogarite.ROLET.index(l["roli"]), horizontal=True,
                             format_func=lambda r: "Admin" if r == "admin" else "Përdorues")
        if st.button("Ruaj rolin"):
            try:
                llogarite.ndrysho_rolin(zgjedhur, roli_i_ri)
                st.success("Roli u ndryshua.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
        with st.form("reset", clear_on_submit=True):
            fj = st.text_input("Fjalëkalim i ri për këtë llogari", type="password")
            if st.form_submit_button("Vendos fjalëkalimin"):
                try:
                    llogarite.ndrysho_fjalekalimin(zgjedhur, fj)
                    st.success("Fjalëkalimi u ndryshua.")
                except ValueError as e:
                    st.error(str(e))
    with t3:
        if zgjedhur == unë:
            st.info("Nuk mund ta fshish llogarinë me të cilën je i futur.")
        else:
            st.warning("Fshihen llogaria, profili dhe të gjitha bisedat. Kjo nuk kthehet pas.")
            if st.checkbox(f"Po, fshije '{zgjedhur}'", key=f"konf_{zgjedhur}"):
                if st.button("Fshi përgjithmonë", type="primary"):
                    try:
                        llogarite.fshi_llogari(zgjedhur)
                        st.success("U fshi.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    pa_llogari = query("MATCH (p:Person) WHERE NOT (:Llogari)-[:ESHTE]->(p) "
                       "OPTIONAL MATCH (p)-[:DERGOI]->(m) RETURN p.id AS id, p.emer AS emer, count(m) AS mesazhe")
    if pa_llogari:
        st.subheader("Persona pa llogari (nga versioni i vjetër)")
        for p in pa_llogari:
            c1, c2 = st.columns([4, 1])
            c1.write(f"{p['emer']} · {p['mesazhe']} mesazhe")
            if c2.button("Fshi", key=f"fshi_p_{p['id']}"):
                db_p.fshi_person(p["id"])
                st.rerun()


# ---------------------------------------------------------------- 💊 Barnat
FUSHAT_E_NDRYSHUESHME = ["emer", "doza", "doza_maks", "kohezgjatja", "si_merret"]


def _ruaj_ne_json(perditesime: dict[str, dict] | None = None, i_ri: dict | None = None):
    """Ndryshimet ruhen edhe te njohurite.json, që `ngarko_grafin.py` të mos i fshijë."""
    data = json.loads(SKEDARI_NJOHURIVE.read_text(encoding="utf-8"))
    for b in data["barnat"]:
        b.update((perditesime or {}).get(b["id"], {}))
    if i_ri:
        data["barnat"].append(i_ri["barna"])
        for s in data["simptomat"]:
            if s["id"] in i_ri["simptomat"] and i_ri["barna"]["id"] not in s["barnat"]:
                s["barnat"].append(i_ri["barna"]["id"])
    SKEDARI_NJOHURIVE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def barnat_faqe():
    st.title("💊 Ilaçet")
    st.caption("Ndryshimet ruhen menjëherë në Neo4j dhe te data/njohurite.json. "
               "Para përdorimit real, çdo ndryshim duhet ta kontrollojë një farmacist.")
    barnat = query("MATCH (b:Barna) OPTIONAL MATCH (s:Simptome)-[:TRAJTOHET_ME]->(b) "
                   "RETURN b.id AS id, b.emer AS emer, b.doza AS doza, b.doza_maks AS doza_maks, "
                   "b.kohezgjatja AS kohezgjatja, b.si_merret AS si_merret, "
                   "collect(s.emer) AS simptomat ORDER BY b.emer")
    ndryshuar = st.data_editor(
        [{**b, "simptomat": ", ".join(b["simptomat"])} for b in barnat], hide_index=True,
        width="stretch", disabled=["id", "simptomat"], key="redaktori_barnave",
        column_config={"id": "ID", "emer": "Emri", "doza": "Doza", "doza_maks": "Maksimumi",
                       "kohezgjatja": "Kohëzgjatja", "si_merret": "Si merret", "simptomat": "Për simptomat"})
    perditesime = {}
    for vjeter, ri in zip(barnat, ndryshuar):
        diff = {f: ri[f] for f in FUSHAT_E_NDRYSHUESHME if ri[f] != vjeter[f]}
        if diff:
            perditesime[vjeter["id"]] = diff
    if perditesime and st.button(f"💾 Ruaj ndryshimet ({len(perditesime)} ilaçe)", type="primary"):
        for bid, diff in perditesime.items():
            query("MATCH (b:Barna {id: $id}) SET b += $diff", id=bid, diff=diff)
        _ruaj_ne_json(perditesime)
        chatbot._te_gjitha_barnat.cache_clear()
        st.success("Ndryshimet u ruajtën.")
        st.rerun()

    st.subheader("Kundërindikimet")
    zgjedhur = st.selectbox("Ilaçi", barnat, format_func=lambda b: b["emer"])
    rows = query("MATCH (b:Barna {id: $id})-[r:KUNDERINDIKOHET_PER|KUJDES_ME]->(g:Gjendje) "
                 "RETURN CASE type(r) WHEN 'KUJDES_ME' THEN '⚠️ Kujdes' ELSE '⛔ Kundërindikim' END AS Lloji, "
                 "g.emer AS Gjendja, r.arsye AS Arsyeja ORDER BY Lloji", id=zgjedhur["id"])
    st.dataframe(rows, hide_index=True, width="stretch")

    with st.expander("➕ Shto ilaç të ri"):
        gjendjet = gjendjet_nga_db()
        simptomat = {r["id"]: r["emer"] for r in query("MATCH (s:Simptome) RETURN s.id AS id, s.emer AS emer ORDER BY s.emer")}
        with st.form("ilac_i_ri"):
            bid = st.text_input("ID (pa hapësira, p.sh. naproksen)")
            emer = st.text_input("Emri, p.sh. Naproksen 220 mg")
            lende = st.text_input("Lënda aktive")
            forma = st.text_input("Forma", value="Tableta")
            tregtare = st.text_input("Emra tregtarë (me presje)")
            doza = st.text_input("Doza (të rritur)")
            maks = st.text_input("Doza maksimale")
            kohe = st.text_input("Kohëzgjatja maksimale pa mjek")
            si = st.text_input("Si merret")
            per = st.multiselect("Për simptomat", list(simptomat), format_func=simptomat.get)
            kunder = st.multiselect("Kundërindikohet për (hiqet automatikisht)", list(gjendjet), format_func=gjendjet.get)
            kujdes = st.multiselect("Kujdes për (shfaqet paralajmërim)", list(gjendjet), format_func=gjendjet.get)
            if st.form_submit_button("Shto ilaçin"):
                bid = bid.strip().lower().replace(" ", "_")
                if not (bid and emer and doza and per):
                    st.error("Plotëso të paktën ID, emrin, dozën dhe simptomat.")
                elif query("MATCH (b:Barna {id: $id}) RETURN 1 AS x", id=bid):
                    st.error("Ky ID ekziston.")
                else:
                    barna = {"id": bid, "emer": emer, "lende_aktive": lende, "forma": forma,
                             "emra_tregtare": [t.strip() for t in tregtare.split(",") if t.strip()] or [emer],
                             "doza": doza, "doza_maks": maks, "kohezgjatja": kohe, "si_merret": si,
                             "paralajmerime": [], "efekte_anesore": [],
                             "kunderindikime": {g: f"Kundërindikohet: {gjendjet[g]}." for g in kunder},
                             "kujdes": {g: f"Kujdes: {gjendjet[g]}. Konsultohu me farmacistin." for g in kujdes}}
                    props = {k: v for k, v in barna.items() if k not in ("kunderindikime", "kujdes")}
                    query("CREATE (b:Barna) SET b = $props", props=props)
                    for tipi, celesi in (("KUNDERINDIKOHET_PER", "kunderindikime"), ("KUJDES_ME", "kujdes")):
                        query(f"MATCH (b:Barna {{id: $id}}) UNWIND $rows AS r MATCH (g:Gjendje {{id: r.g}}) "
                              f"MERGE (b)-[x:{tipi}]->(g) SET x.arsye = r.a", id=bid,
                              rows=[{"g": g, "a": a} for g, a in barna[celesi].items()])
                    query("MATCH (b:Barna {id: $id}) UNWIND $per AS sid MATCH (s:Simptome {id: sid}) "
                          "OPTIONAL MATCH (s)-[t:TRAJTOHET_ME]->() WITH b, s, count(t) AS n "
                          "MERGE (s)-[r:TRAJTOHET_ME]->(b) SET r.rendi = n", id=bid, per=per)
                    _ruaj_ne_json(i_ri={"barna": barna, "simptomat": per})
                    chatbot._te_gjitha_barnat.cache_clear()
                    st.success(f"'{emer}' u shtua.")
                    st.rerun()


# ---------------------------------------------------------------- 💾 Backup
def backup_faqe():
    st.title("💾 Backup dhe Neo4j Desktop")
    st.subheader("Backup në Desktop")
    st.write(f"Ruan gjithë databazën te `{backup.DOSJA_BACKUP}`: `databaza.json` dhe `databaza.cypher` "
             "(skript që e rikrijon databazën në Neo4j Desktop ose në çdo Neo4j tjetër).")
    if st.button("💾 Bëj backup tani", type="primary"):
        with st.spinner("Po eksportoj..."):
            dosja = backup.ruaj_backup()
        st.success(f"U ruajt te: {dosja}")
    if backup.DOSJA_BACKUP.exists():
        te_fundit = sorted((d for d in backup.DOSJA_BACKUP.iterdir() if d.is_dir()), reverse=True)[:5]
        if te_fundit:
            st.caption("Backup-et e fundit: " + ", ".join(d.name for d in te_fundit))

    st.subheader("🗄️ Databaza aktive")
    st.markdown(f"`{os.getenv('NEO4J_URI')}` · lidhja **{menyra_lidhjes().upper()}**")
    st.markdown(
        "Databaza lokale ndodhet te `chatbot_industri/neo4j_local` dhe niset vetë nga ikona **FarmaBot** në Desktop.\n\n"
        "**Ta shohësh në Neo4j Desktop:** *Connect* → *Remote connection* → URL `bolt://127.0.0.1:7687`, "
        "përdoruesi `neo4j`, fjalëkalimi nga `.env` (`NEO4J_PASSWORD`).\n\n"
        "**Në shfletues:** http://localhost:7474 (Neo4j Browser).")
    if backup.ka_lokal():
        st.subheader("Kopje në një databazë tjetër lokale")
        st.write(f"Destinacioni: `{os.getenv('NEO4J_LOCAL_URI')}`. Përmbajtja e tij zëvendësohet.")
        if st.checkbox("E kuptoj që të dhënat e destinacionit zëvendësohen"):
            if st.button("🔄 Kopjo databazën aktive atje"):
                with st.spinner("Po kopjoj..."):
                    try:
                        r = backup.kopjo_ne_lokal()
                        st.success(f"U kopjuan {r['nyje']} nyje dhe {r['lidhje']} lidhje.")
                    except Exception as e:
                        st.error(f"Nuk u lidh: {e}")
