"""Paneli i përdoruesit: llogaria ime, historia ime, fshirja e të dhënave."""
import streamlit as st

import llogarite
import perdoruesit as db_p
from faqet.stili import IKONA
from faqet.perbashket import gjendjet_nga_db, perdoruesi
from faqet.teksti import t


def faqja():
    llogaria = perdoruesi()
    if not llogaria:
        st.info(t("hyr_per_faqen"))
        return
    st.title("👤 " + t("llogaria_ime"))
    person = db_p.merr_person(llogaria["person_id"]) if llogaria["person_id"] else None
    gjendjet = gjendjet_nga_db()

    k1, k2, k3 = st.columns(3)
    k1.metric(t("perdoruesi"), llogaria["perdoruesi"])
    k2.metric(t("roli"), "Admin" if llogaria["roli"] == "admin" else t("perdorues_thjeshte"))
    k3.metric(t("mesazhe_ruajtura"), len(db_p.historia(llogaria["person_id"], 10_000)) if person else 0)

    if person:
        st.subheader(t("profili_ruajtur"))
        st.markdown(f"**{t('emri')}:** {person['emer']}  \n**{t('mosha')}:** {person['mosha'] if person['mosha'] is not None else '–'}  \n"
                    f"**{t('gjendje')}:** {', '.join(gjendjet.get(g, g) for g in person['gjendjet']) or '–'}  \n"
                    f"**{t('alergji_shkurt')}:** {person['shenime'] or '–'}")
        st.caption(t("ndrysho_profilin"))

        st.subheader(t("historia"))
        historia = db_p.historia(llogaria["person_id"], 200)
        if not historia:
            st.info(t("pa_histori"))
        for m in historia:
            with st.chat_message(m["role"], avatar=IKONA if m["role"] == "assistant" else None):
                st.caption(m["ora"][:16].replace("T", " "))
                st.markdown(m["content"])

    st.subheader(t("ndrysho_fj"))
    with st.form("fjalekalimi", clear_on_submit=True):
        aktual = st.text_input(t("fj_aktual"), type="password")
        i_ri = st.text_input(t("fj_ri"), type="password")
        perserit = st.text_input(t("fj_perserit"), type="password")
        if st.form_submit_button(t("ndrysho")):
            if not llogarite.hyr(llogaria["perdoruesi"], aktual):
                st.error(t("fj_gabim"))
            elif i_ri != perserit:
                st.error(t("fj_nuk_perputhen"))
            else:
                try:
                    llogarite.ndrysho_fjalekalimin(llogaria["perdoruesi"], i_ri)
                    st.success(t("fj_ndryshoi"))
                except ValueError as e:
                    st.error(str(e))

    if llogaria["roli"] != "admin":
        st.subheader(t("fshi_titull"))
        st.caption(t("fshi_shenim"))
        if st.checkbox(t("fshi_konfirmo")):
            if st.button(t("fshi_btn"), type="primary"):
                llogarite.fshi_llogari(llogaria["perdoruesi"])
                for k in [k for k in st.session_state if k not in ("paneli_hapur", "gjuha", "tema")]:
                    del st.session_state[k]
                st.rerun()
