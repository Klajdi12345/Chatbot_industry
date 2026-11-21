"""Faqja e bisedës, e njëjtë për përdoruesit, adminët dhe vizitorët anonimë."""
import os
import time

import streamlit as st

import claude_ai
import config
import perdoruesit as db_p
from chatbot import Konteksti, Profili, gjuha_e_bisedes, pergjigju
from faqet.stili import IKONA, stili_motorit
from faqet.perbashket import (AUTOMATIKE, apliko_ne_pritje, gjendjet_nga_db, perdoruesi,
                              shfaq_kartat, vendos_me_vone)


def _ngarko_profilin(pid: str | None, gjendjet: dict[str, str]):
    """Mbush panelin dhe bisedën nga databaza (një herë për sesion)."""
    person = db_p.merr_person(pid) if pid else None
    vendos_me_vone(mosha=person["mosha"] if person else None,
                   shenime=(person["shenime"] or "") if person else "",
                   **{f"gj_{gid}": bool(person and gid in person["gjendjet"]) for gid in gjendjet})
    st.session_state.mesazhet = db_p.historia(pid) if pid else []
    st.session_state.simptomat = db_p.simptomat_e_fundit(pid) if pid else []
    st.session_state.barnat_e_fundit = db_p.barnat_e_fundit(pid) if pid else []
    st.session_state.pritje, st.session_state.pritje_shto = [], False
    st.session_state.profili_ngarkuar = pid
    st.session_state._kopje_profili = {}


SHEMBUJ = [("🦷", "Më dhemb dhëmbi"), ("🤒", "Kam temperaturë dhe grip"),
           ("🤧", "Teshtij shumë dhe më lotojnë sytë"), ("🔥", "Më djeg stomaku pas ngrënies")]


def _avatar(roli: str) -> str:
    return IKONA if roli == "assistant" else "🧑"


def _kohezgjatja(sekonda: float, gjuha: str = "sq") -> str:
    if sekonda < 60:
        if gjuha == "en":
            return f"{sekonda:.0f} seconds" if sekonda >= 2 else "1 second"
        return f"{sekonda:.0f} sekonda" if sekonda >= 2 else "1 sekondë"
    return f"{int(sekonda // 60)} min {int(sekonda % 60)} s"


def _titulli_mendimit(p) -> str:
    gjuha = getattr(p, "gjuha", "sq")
    return ("🧠 Thought for " if gjuha == "en" else "🧠 Mendoi për ") + _kohezgjatja(p.sekonda, gjuha)


def _shfaq_mendimin(p):
    """Paneli i mbyllur "🧠 Mendoi për ..." mbi përgjigje (si te Claude)."""
    if not p or not getattr(p, "hapat", None):
        return
    with st.expander(_titulli_mendimit(p)):
        st.markdown("\n".join(f"- {h}" for h in p.hapat))
        if p.mendimi_modelit:
            st.caption("Model reasoning:" if getattr(p, "gjuha", "sq") == "en" else "Arsyetimi i modelit:")
            st.text(p.mendimi_modelit[-4000:])


MOTORET = {"claude": "✨ Claude AI", "ollama": "💻 Lokal (Ollama)"}
NIVELET = {"low": "⚡ I shpejtë", "medium": "⚖️ I balancuar", "high": "🎯 Më i saktë"}


def _paneli_motorit() -> str:
    """Zgjedhja e motorit gjuhësor për këtë sesion (Claude ose modeli lokal)."""
    ka_claude = claude_ai.ka_kredenciale()
    st.session_state.setdefault("motori", config.motori_parazgjedhur())
    with st.expander("🤖 Motori AI", expanded=False):
        st.radio("Motori", list(MOTORET), format_func=MOTORET.get, key="motori", horizontal=True,
                 label_visibility="collapsed")
        if st.session_state.motori == "claude":
            if not ka_claude:
                st.warning("Mungon `ANTHROPIC_API_KEY` te `.env`. Shto çelësin dhe rinise aplikacionin.")
            st.session_state.setdefault("efforti", claude_ai.EFFORT if claude_ai.EFFORT in NIVELET else "medium")
            st.select_slider("Përpjekja e mendimit", list(NIVELET), format_func=NIVELET.get, key="efforti",
                             help="Sa thellë mendon Claude te “🧠 Mendo më thellë”. Më i saktë = më i ngadaltë.")
            st.caption(f"Modeli: `{claude_ai.MODEL}` · 📷 mund të dërgosh edhe foto të ilaçit. "
                       "Mesazhet dërgohen te Anthropic: mos shkruaj emra ose të dhëna që të identifikojnë.")
        else:
            st.caption(f"Modeli lokal: `{config.LLM_MODEL}`. Asgjë nuk del nga kompjuteri.")
    motori = st.session_state.motori
    if motori == "claude" and not ka_claude:
        motori = "ollama"
    config.vendos_motorin(motori, st.session_state.get("efforti"))
    return motori


def _eksporto(mesazhet: list[dict]) -> str:
    rreshta = ["# Biseda me FarmaBot", "", f"_{time.strftime('%Y-%m-%d %H:%M')}_", ""]
    for m in mesazhet:
        rreshta += [f"**{'Ti' if m['role'] == 'user' else 'FarmaBot'}:**", "", m["content"], ""]
    rreshta.append("_Informacion i përgjithshëm, jo zëvendësim i mjekut ose farmacistit._")
    return "\n".join(rreshta)


def _pyetja_nga_foto(foto, tekst: str, en: bool) -> tuple[str, str]:
    """Claude Vision lexon foton; emrat e lexuar i shtohen pyetjes, që baza të gjejë ilaçin
    dhe të kontrollojë profilin (dozat vijnë gjithmonë nga databaza)."""
    lloji = foto.type or claude_ai.LLOJET_FOTO.get(foto.name.rsplit(".", 1)[-1].lower(), "image/jpeg")
    d = claude_ai.lexo_foton(foto.getvalue(), lloji, tekst)
    emrat = list(dict.fromkeys(d["emrat_tregtare"] + d["lende_aktive"]))
    if not d["eshte_ilac"] or not emrat:
        shenim = d["pershkrim"] or ("I could not read a medicine in the photo." if en
                                    else "Nuk lexova dot një ilaç në foto.")
        return tekst, shenim
    forca = f" {d['forca']}" if d["forca"] else ""
    shenim = ("📷 In the photo: " if en else "📷 Në foto: ") + ", ".join(emrat) + forca
    if tekst:
        pyetja = tekst if any(e.lower() in tekst.lower() for e in emrat) else f"{tekst} ({', '.join(emrat)})"
    elif en:
        pyetja = f"What is {' / '.join(emrat)} and how do I take it?"
    else:
        pyetja = f"Çfarë është {' / '.join(emrat)} dhe si merret?"
    return pyetja, shenim


def faqja():
    gjendjet = gjendjet_nga_db()
    llogaria = perdoruesi()
    pid = llogaria["person_id"] if llogaria else None

    st.session_state.setdefault("mesazhet", [])
    st.session_state.setdefault("simptomat", [])
    st.session_state.setdefault("barnat_e_fundit", [])
    st.session_state.setdefault("pritje", [])
    st.session_state.setdefault("pritje_shto", False)
    st.session_state.setdefault("mosha", None)
    if st.session_state.get("profili_ngarkuar", "∅") != pid:
        _ngarko_profilin(pid, gjendjet)
        st.rerun()
    # Streamlit i fshin vlerat e widget-eve kur kalon në një faqe tjetër: rikthei nga kopja.
    for k, v in st.session_state.get("_kopje_profili", {}).items():
        st.session_state.setdefault(k, v)
    apliko_ne_pritje()

    with st.sidebar:
        st.header("🩺 Profili")
        if not pid:
            st.caption("Je pa llogari: asgjë nuk ruhet. Hyr ose regjistrohu për ta ruajtur profilin.")
        mosha = st.number_input("Mosha", min_value=0, max_value=110, step=1, key="mosha",
                                placeholder="p.sh. 30")
        zgjedhura = set()
        with st.expander("Gjendje dhe ilaçe që merr", expanded=True):
            for gid, emer in gjendjet.items():
                if gid not in AUTOMATIKE and st.checkbox(emer, key=f"gj_{gid}"):
                    zgjedhura.add(gid)
        st.session_state.setdefault("mendo", os.getenv("FARMABOT_MENDO", "1") != "0")
        st.toggle("🧠 Mendo më thellë", key="mendo",
                  help="Bota e rilexon mesazhin me një model që mendon (si Claude), e kontrollon në bazë "
                       "dhe të tregon hapat. Zgjat nga disa sekonda deri në 1–2 minuta. "
                       "Urgjencat përgjigjen gjithmonë menjëherë.")
        shenime = st.text_area("Alergji ose ilaçe të tjera", key="shenime",
                               placeholder="p.sh. alergji nga penicilina")
        st.session_state._kopje_profili = {
            "mosha": mosha, "shenime": shenime,
            **{f"gj_{gid}": gid in zgjedhura for gid in gjendjet if gid not in AUTOMATIKE}}
        motori = _paneli_motorit()
        if pid and st.button("💾 Ruaj profilin", width="stretch"):
            db_p.perditeso_person(pid, mosha=int(mosha) if mosha is not None else None,
                                  gjendjet=zgjedhura, shenime=shenime)
            st.toast("Profili u ruajt.")
        if st.button("🆕 Bisedë e re", width="stretch",
                     help="Fillon nga e para. Nuk është e nevojshme: mund të vazhdosh me një temë tjetër në të njëjtën bisedë."):
            st.session_state.mesazhet = []
            st.session_state.simptomat = []
            st.session_state.barnat_e_fundit = []
            st.session_state.pritje, st.session_state.pritje_shto = [], False
            st.rerun()
        if st.session_state.mesazhet:
            st.download_button("⬇️ Shkarko bisedën", _eksporto(st.session_state.mesazhet),
                               file_name=f"farmabot_{time.strftime('%Y%m%d_%H%M')}.md", mime="text/markdown",
                               width="stretch")

    profili = Profili(mosha=int(mosha) if mosha is not None else None,
                      gjendjet=zgjedhura, shenime=(shenime or "").strip())

    st.markdown(f'## Si ndihesh sot? {stili_motorit(config.emri_motorit(), motori)}', unsafe_allow_html=True)
    st.caption("ℹ️ Informacion i përgjithshëm për ilaçe pa recetë, jo zëvendësim i mjekut ose farmacistit. "
               "Në urgjencë telefono **127** ose **112**.")

    for m in st.session_state.mesazhet:
        with st.chat_message(m["role"], avatar=_avatar(m["role"])):
            _shfaq_mendimin(m.get("pergjigje"))
            if m.get("foto"):
                st.image(m["foto"], width=220)
            if m.get("urgjence"):
                st.error(m["content"])
            else:
                st.markdown(m["content"])
            if m.get("pergjigje"):
                shfaq_kartat(m["pergjigje"])

    if not st.session_state.mesazhet:
        st.markdown("Shkruaj simptomat poshtë, ose provo një nga këto:")
        kolonat = st.columns(len(SHEMBUJ))
        for kol, (ikona, tekst) in zip(kolonat, SHEMBUJ):
            if kol.button(f"{ikona} {tekst}", width="stretch"):
                st.session_state._shembull = tekst
                st.rerun()

    me_foto = motori == "claude"
    hyrja = st.chat_input("Përshkruaj simptomat, p.sh. “më dhemb koka prej dy ditësh”"
                          + (" · 📎 ose dërgo foton e ilaçit" if me_foto else "") + " · You can also write in English",
                          accept_file=me_foto, file_type=list(claude_ai.LLOJET_FOTO) if me_foto else None)
    foto = None
    if hyrja is not None and not isinstance(hyrja, str):
        foto = hyrja.files[0] if hyrja.files else None
        hyrja = (hyrja.text or "").strip()
    pyetja = hyrja or st.session_state.pop("_shembull", None) or ""
    if not pyetja and not foto:
        return
    with st.chat_message("user", avatar=_avatar("user")):
        if foto:
            st.image(foto.getvalue(), width=220)
        if pyetja:
            st.markdown(pyetja)
    historia = [{"role": m["role"], "content": m["content"]} for m in st.session_state.mesazhet]
    shenim_foto = ""
    if foto:
        with st.spinner("📷 Claude po lexon foton..."):
            try:
                en_foto = bool(pyetja) and gjuha_e_bisedes(pyetja, historia) == "en"
                pyetja, shenim_foto = _pyetja_nga_foto(foto, pyetja, en_foto)
            except Exception as e:
                st.error(f"Nuk e lexova dot foton: {e}")
                st.stop()
        if not pyetja:
            with st.chat_message("assistant", avatar=_avatar("assistant")):
                st.markdown(shenim_foto)
            st.session_state.mesazhet.append({"role": "user", "content": "(foto)", "foto": foto.getvalue()})
            st.session_state.mesazhet.append({"role": "assistant", "content": shenim_foto})
            return
    with st.chat_message("assistant", avatar=_avatar("assistant")):
        mendo = bool(st.session_state.get("mendo"))
        en = gjuha_e_bisedes(pyetja, historia) == "en"
        etiketa = ("🧠 Thinking..." if en else "🧠 Po mendoj...") if mendo else \
            ("Searching the knowledge base..." if en else "Po kërkoj në bazën e njohurive...")
        statusi = st.status(etiketa, expanded=mendo)
        with statusi:
            vendi_hapave = st.container()
            vendi_mendimit = st.empty()
        mendimi = {"tekst": "", "ora": 0.0}

        def on_hap(tekst):
            vendi_hapave.markdown(f"- {tekst}")
            statusi.update(label=tekst if len(tekst) < 90 else tekst[:87] + "...")

        def on_mendim(copa):
            mendimi["tekst"] += copa
            if time.perf_counter() - mendimi["ora"] > 0.3:  # mos e rifresko ndërfaqen për çdo fjalë
                mendimi["ora"] = time.perf_counter()
                vendi_mendimit.caption(mendimi["tekst"][-1200:])

        try:
            konteksti = Konteksti(simptomat=st.session_state.simptomat,
                                  barnat=st.session_state.barnat_e_fundit,
                                  pritje=st.session_state.pritje, pritje_shto=st.session_state.pritje_shto)
            p = pergjigju(pyetja, historia, profili, konteksti=konteksti, mendo=mendo,
                          on_hap=on_hap, on_mendim=on_mendim)
        except Exception as e:
            statusi.update(label="An error occurred" if en else "Ndodhi një gabim", state="error")
            st.error(f"Ndodhi një gabim: {e}\n\nKontrollo që Neo4j dhe Ollama (embeddings) janë ndezur"
                     + (" dhe që çelësi i Claude është i saktë." if motori == "claude" else "."))
            st.stop()
        vendi_mendimit.empty()
        statusi.update(label=_titulli_mendimit(p), state="complete", expanded=False)
        if shenim_foto:
            st.caption(shenim_foto)
        if p.urgjence:
            st.error(p.tekst)
        else:
            st.markdown(p.tekst)
        shfaq_kartat(p)
    st.session_state.mesazhet.append({"role": "user", "content": pyetja,
                                      **({"foto": foto.getvalue()} if foto else {})})
    st.session_state.mesazhet.append({"role": "assistant", "content": p.tekst,
                                      "urgjence": p.urgjence, "pergjigje": p})
    # Konteksti i bisedës: biseda vazhdon pa u rinisur (pyetje vijuese, "kam edhe...", përgjigje sqaruese).
    if p.simptomat:
        st.session_state.simptomat = [s["id"] for s in p.simptomat]
    if p.barnat_konteksti:
        st.session_state.barnat_e_fundit = p.barnat_konteksti
    if not p.urgjence:
        st.session_state.pritje, st.session_state.pritje_shto = p.pritje, p.pritje_shto

    if pid:
        db_p.ruaj_mesazh(pid, "user", pyetja)
        db_p.ruaj_mesazh(pid, "assistant", p.tekst, [s["id"] for s in p.simptomat],
                         [b["id"] for b in p.barnat] or p.barnat_konteksti)
        db_p.shto_gjendje(pid, p.gjendje_te_reja)
        if p.mosha_e_re is not None and profili.mosha is None:
            db_p.perditeso_person(pid, mosha=p.mosha_e_re)
    # Gjendjet/mosha nga biseda shfaqen në panel dhe vlejnë për pyetjet e ardhshme. Mosha nga
    # mesazhi ("djali 5 vjeç") zëvendëson atë të panelit, që fëmija të mos marrë doza për të rritur
    # (në databazë nuk mbishkruhet mosha e llogarisë).
    if p.gjendje_te_reja or (p.mosha_e_re is not None and p.mosha_e_re != profili.mosha):
        vendos_me_vone(**{f"gj_{gid}": True for gid in p.gjendje_te_reja})
        if p.mosha_e_re is not None:
            vendos_me_vone(mosha=p.mosha_e_re)
        st.rerun()
