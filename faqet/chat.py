"""Faqja e bisedës (në stilin e Claude.ai), e njëjtë për përdoruesit, adminët dhe vizitorët anonimë.

Paneli anësor ka seksione që hapen e mbyllen (Profili, Gjendjet, Cilësimet); gjendja e tyre mbahet
gjatë sesionit. I gjithë paneli hapet/mbyllet me ☰ sipër."""
import base64
import os
import time

import streamlit as st

import perdoruesit as db_p
from chatbot import Konteksti, Profili, gjuha_e_bisedes, pergjigju
from faqet.perbashket import (AUTOMATIKE, apliko_ne_pritje, gjendjet_nga_db, perdoruesi,
                              shfaq_kartat, vendos_me_vone)
from faqet.stili import IKONA
from faqet.teksti import pershendetja, t


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


def _avatar(roli: str) -> str | None:
    return IKONA if roli == "assistant" else None  # përdoruesi: flluskë pa avatar (si te Claude)


def _kohezgjatja(sekonda: float, gj: str = "sq") -> str:
    if sekonda < 60:
        if gj == "en":
            return f"{sekonda:.0f} seconds" if sekonda >= 2 else "1 second"
        return f"{sekonda:.0f} sekonda" if sekonda >= 2 else "1 sekondë"
    return f"{int(sekonda // 60)} min {int(sekonda % 60)} s"


def _titulli_mendimit(p) -> str:
    gj = getattr(p, "gjuha", "sq")
    return ("🧠 Thought for " if gj == "en" else "🧠 Mendoi për ") + _kohezgjatja(p.sekonda, gj)


def _shfaq_mendimin(p):
    """Paneli i mbyllur "🧠 Mendoi për ..." mbi përgjigje."""
    if not p or not getattr(p, "hapat", None):
        return
    with st.expander(_titulli_mendimit(p)):
        st.markdown("\n".join(f"- {h}" for h in p.hapat))
        if p.mendimi_modelit:
            st.caption("Model reasoning:" if getattr(p, "gjuha", "sq") == "en" else "Arsyetimi i modelit:")
            st.text(p.mendimi_modelit[-4000:])


def _eksporto(mesazhet: list[dict]) -> str:
    rreshta = ["# FarmaBot", "", f"_{time.strftime('%Y-%m-%d %H:%M')}_", ""]
    for m in mesazhet:
        rreshta += [f"**{t('ti') if m['role'] == 'user' else 'FarmaBot'}:**", "", m["content"], ""]
    return "\n".join(rreshta)


def _bisede_e_re():
    st.session_state.mesazhet = []
    st.session_state.simptomat = []
    st.session_state.barnat_e_fundit = []
    st.session_state.pritje, st.session_state.pritje_shto = [], False


def _seksion(emri: str, titulli: str, hapur: bool = True):
    """Seksion i panelit që hapet/mbyllet dhe e mban gjendjen gjatë sesionit."""
    celesi = f"seksioni_{emri}"
    st.session_state.setdefault(celesi, hapur)
    return st.expander(titulli, key=celesi, on_change="rerun")


def _paneli(gjendjet: dict[str, str], pid: str | None) -> tuple[Profili, set]:
    with st.sidebar:
        st.button(t("biseda_re"), width="stretch", type="primary", on_click=_bisede_e_re, help=t("biseda_re_help"))

        with _seksion("profili", f"🩺 {t('profili')}"):
            if not pid:
                st.caption(t("pa_llogari_shenim"))
            mosha = st.number_input(t("mosha"), min_value=0, max_value=110, step=1, key="mosha",
                                    placeholder=t("mosha_ph"))
            shenime = st.text_area(t("alergji"), key="shenime", placeholder=t("alergji_ph"))

        zgjedhura = set()
        with _seksion("gjendjet", f"💊 {t('gjendjet')}", hapur=False):
            for gid, emer in gjendjet.items():
                if gid not in AUTOMATIKE and st.checkbox(emer, key=f"gj_{gid}"):
                    zgjedhura.add(gid)

        with _seksion("cilesimet", f"⚙️ {t('cilesimet')}", hapur=False):
            st.session_state.setdefault("mendo", os.getenv("FARMABOT_MENDO", "1") != "0")
            st.toggle(t("mendo"), key="mendo", help=t("mendo_help"))
            if st.session_state.mesazhet:
                st.download_button(t("shkarko"), _eksporto(st.session_state.mesazhet),
                                   file_name=f"farmabot_{time.strftime('%Y%m%d_%H%M')}.md", mime="text/markdown",
                                   width="stretch")

        st.session_state._kopje_profili = {
            "mosha": mosha, "shenime": shenime,
            **{f"gj_{gid}": gid in zgjedhura for gid in gjendjet if gid not in AUTOMATIKE}}
        if pid and st.button(t("ruaj_profilin"), width="stretch"):
            db_p.perditeso_person(pid, mosha=int(mosha) if mosha is not None else None,
                                  gjendjet=zgjedhura, shenime=shenime)
            st.toast(t("profili_u_ruajt"))
    profili = Profili(mosha=int(mosha) if mosha is not None else None,
                      gjendjet=zgjedhura, shenime=(shenime or "").strip())
    return profili, zgjedhura


def _pershendetja(llogaria: dict | None):
    """Ekrani bosh: përshëndetje e madhe në mes dhe shembuj (si faqja e re te Claude.ai)."""
    emri = ""
    if llogaria and llogaria.get("person_id"):
        person = db_p.merr_person(llogaria["person_id"])
        emri = ((person or {}).get("emer") or llogaria["perdoruesi"]).split()[0]
    ikona = base64.b64encode(open(IKONA, "rb").read()).decode()
    teksti = f"{pershendetja()}, {emri}" if emri else t("si_ndihesh")
    st.markdown(f'<div class="fb-pershendetje"><img src="data:image/png;base64,{ikona}" alt="">'
                f'<span>{teksti}</span><p>{t("paralajmerim")}</p></div>', unsafe_allow_html=True)
    shembujt = t("shembuj")
    kolonat = st.columns(2)
    for i, (ikona_sh, tekst) in enumerate(shembujt):
        if kolonat[i % 2].button(f"{ikona_sh} {tekst}", width="stretch", key=f"shembull_{i}"):
            st.session_state._shembull = tekst
            st.rerun()


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

    profili, _ = _paneli(gjendjet, pid)
    st.markdown('<div class="fb-biseda"></div>', unsafe_allow_html=True)  # kolonë e ngushtë në mes

    if not st.session_state.mesazhet:
        _pershendetja(llogaria)
    else:
        st.caption("ℹ️ " + t("shenim_mjeku"))

    for m in st.session_state.mesazhet:
        with st.chat_message(m["role"], avatar=_avatar(m["role"])):
            _shfaq_mendimin(m.get("pergjigje"))
            if m.get("urgjence"):
                st.error(m["content"])
            else:
                st.markdown(m["content"])
            if m.get("pergjigje"):
                shfaq_kartat(m["pergjigje"])

    pyetja = st.chat_input(t("fusha"))
    pyetja = pyetja or st.session_state.pop("_shembull", None)
    if not pyetja:
        return
    with st.chat_message("user", avatar=_avatar("user")):
        st.markdown(pyetja)
    historia = [{"role": m["role"], "content": m["content"]} for m in st.session_state.mesazhet]
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
            statusi.update(label=t("gabim"), state="error")
            st.error(f"{t('gabim')}: {e}\n\n{t('gabim_sherbime')}")
            st.stop()
        vendi_mendimit.empty()
        statusi.update(label=_titulli_mendimit(p), state="complete", expanded=False)
        if p.urgjence:
            st.error(p.tekst)
        else:
            st.markdown(p.tekst)
        shfaq_kartat(p)
    st.session_state.mesazhet.append({"role": "user", "content": pyetja})
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
    elif len(st.session_state.mesazhet) == 2:
        st.rerun()  # largon përshëndetjen e ekranit bosh pas mesazhit të parë
