"""Paneli i përdoruesit: llogaria ime, historia ime, fshirja e të dhënave."""
import streamlit as st

import llogarite
import perdoruesit as db_p
from faqet.perbashket import gjendjet_nga_db, perdoruesi


def faqja():
    llogaria = perdoruesi()
    if not llogaria:
        st.info("Hyr në llogari për ta parë këtë faqe.")
        return
    st.title("👤 Llogaria ime")
    person = db_p.merr_person(llogaria["person_id"]) if llogaria["person_id"] else None
    gjendjet = gjendjet_nga_db()

    k1, k2, k3 = st.columns(3)
    k1.metric("Përdoruesi", llogaria["perdoruesi"])
    k2.metric("Roli", "Admin" if llogaria["roli"] == "admin" else "Përdorues")
    k3.metric("Mesazhe të ruajtura", len(db_p.historia(llogaria["person_id"], 10_000)) if person else 0)

    if person:
        st.subheader("Profili i ruajtur")
        st.markdown(f"**Emri:** {person['emer']}  \n**Mosha:** {person['mosha'] if person['mosha'] is not None else '–'}  \n"
                    f"**Gjendje:** {', '.join(gjendjet.get(g, g) for g in person['gjendjet']) or '–'}  \n"
                    f"**Alergji / ilaçe të tjera:** {person['shenime'] or '–'}")
        st.caption("Profilin e ndryshon te paneli majtas i faqes 💬 Biseda, me butonin 💾 Ruaj profilin.")

        st.subheader("Historia e bisedave")
        historia = db_p.historia(llogaria["person_id"], 200)
        if not historia:
            st.info("Nuk ke ende biseda të ruajtura.")
        for m in historia:
            with st.chat_message(m["role"]):
                st.caption(m["ora"][:16].replace("T", " "))
                st.markdown(m["content"])

    st.subheader("🔑 Ndrysho fjalëkalimin")
    with st.form("fjalekalimi", clear_on_submit=True):
        aktual = st.text_input("Fjalëkalimi aktual", type="password")
        i_ri = st.text_input("Fjalëkalimi i ri (min. 8 karaktere)", type="password")
        perserit = st.text_input("Përsërit fjalëkalimin e ri", type="password")
        if st.form_submit_button("Ndrysho"):
            if not llogarite.hyr(llogaria["perdoruesi"], aktual):
                st.error("Fjalëkalimi aktual nuk është i saktë.")
            elif i_ri != perserit:
                st.error("Fjalëkalimet e reja nuk përputhen.")
            else:
                try:
                    llogarite.ndrysho_fjalekalimin(llogaria["perdoruesi"], i_ri)
                    st.success("Fjalëkalimi u ndryshua.")
                except ValueError as e:
                    st.error(str(e))

    if llogaria["roli"] != "admin":
        st.subheader("🗑️ Fshi llogarinë dhe të dhënat")
        st.caption("Fshihen llogaria, profili dhe të gjitha bisedat e tua. Kjo nuk kthehet pas.")
        if st.checkbox("E kuptoj, dua t'i fshij të gjitha të dhënat e mia"):
            if st.button("Fshi përgjithmonë", type="primary"):
                llogarite.fshi_llogari(llogaria["perdoruesi"])
                st.session_state.clear()
                st.rerun()
