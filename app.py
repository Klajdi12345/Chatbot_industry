"""FarmaBot: hyrja, rolet dhe navigimi.   Nis me:  streamlit run app.py

Rolet:
  * vizitor (pa llogari) → vetëm biseda, asgjë nuk ruhet
  * përdorues           → biseda + llogaria ime (profili dhe historia ruhen në Neo4j)
  * admin               → gjithçka + përmbledhje, përdoruesit, ilaçet, backup
"""
import streamlit as st

import llogarite
import perdoruesit as db_p
from faqet import admin, chat, profili
from faqet import stili
from faqet.perbashket import perdoruesi

st.set_page_config(page_title="FarmaBot", page_icon=stili.IKONA, layout="wide")
stili.apliko()


@st.cache_resource
def pergatit_databazen():
    db_p.krijo_skemen()
    return llogarite.sigurohu_per_admin()  # fjalëkalimi vetëm herën e parë (ruhet te .env)


def _hero() -> str:
    import base64
    ikona = base64.b64encode(open(stili.IKONA, "rb").read()).decode()
    veti = [("🩺", "Nga simptoma te ilaçi", "Shkruaj si ndihesh, p.sh. “më dhemb dhëmbi”."),
            ("🛡️", "I sigurt për profilin tënd", "Heq ilaçet që nuk të përshtaten: shtatzëni, ulçerë, ilaçe që merr."),
            ("🚑", "Di kur duhet mjeku", "Shenjat e rrezikut të çojnë te 127 / 112, jo te ilaçet.")]
    rreshta = "".join(f'<div class="fb-veti"><div style="font-size:1.4rem">{i}</div><div><b>{t}</b>'
                      f'<span>{d}</span></div></div>' for i, t, d in veti)
    return (f'<div class="fb-hero"><img src="data:image/png;base64,{ikona}" alt="FarmaBot">'
            f'<h1>FarmaBot</h1><p>Asistenti yt i farmacisë, në shqip.</p>{rreshta}'
            f'<div class="fb-paralajmerim">Informacion i përgjithshëm për ilaçe pa recetë. '
            f'Nuk zëvendëson mjekun ose farmacistin.</div></div>')


def faqja_hyrjes():
    majtas, djathtas = st.columns([1.1, 1], gap="large")
    with majtas:
        st.markdown(_hero(), unsafe_allow_html=True)
    with djathtas:
        st.markdown("### Mirë se erdhe 👋")
        st.caption("Hyr në llogari që profili dhe bisedat të ruhen, ose vazhdo si vizitor.")
        hyr, regj = st.tabs(["🔐 Hyr", "📝 Regjistrohu"])
        with hyr:
            with st.form("hyrja"):
                u = st.text_input("Emri i përdoruesit")
                fj = st.text_input("Fjalëkalimi", type="password")
                if st.form_submit_button("Hyr", type="primary", width="stretch"):
                    llogaria = llogarite.hyr(u, fj)
                    if llogaria:
                        st.session_state.clear()
                        st.session_state.llogaria = llogaria
                        st.rerun()
                    st.error("Emri ose fjalëkalimi nuk është i saktë.")
        with regj:
            with st.form("regjistrimi"):
                u = st.text_input("Emri i përdoruesit", placeholder="p.sh. ëndrra_çela ose john.smith",
                                  help="3–30 karaktere: shkronja shqipe ose angleze (edhe ç, ë), shifra dhe _ . -")
                emer = st.text_input("Emri yt ose një pseudonim", placeholder="p.sh. Arbëreshë Çela",
                                     help="Opsional. Shkronja shqipe ose angleze, hapësira, ' . -")
                mosha = st.number_input("Mosha", min_value=0, max_value=110, value=None, step=1)
                fj = st.text_input("Fjalëkalimi (min. 8 karaktere)", type="password")
                fj2 = st.text_input("Përsërit fjalëkalimin", type="password")
                pelqim = st.checkbox("Pranoj që profili dhe bisedat e mia të ruhen në databazë. "
                                     "Mund t'i fshij kur të dua te 👤 Llogaria ime.")
                st.caption("Mund të përdorësh shkronjat shqipe **ç, ë** dhe ato angleze. "
                           "Emri i përdoruesit nuk dallon shkronjat e mëdha nga të voglat.")
                if st.form_submit_button("Krijo llogarinë", width="stretch"):
                    gabim = llogarite.valido(u, fj) or llogarite.valido_emrin(emer)
                    if gabim:
                        st.error(gabim)
                    elif fj != fj2:
                        st.error("Fjalëkalimet nuk përputhen.")
                    elif not pelqim:
                        st.error("Duhet pëlqimi për të ruajtur të dhënat.")
                    else:
                        try:
                            llogarite.krijo_llogari(u, fj, "perdorues", emer or None,
                                                    int(mosha) if mosha is not None else None)
                            st.session_state.clear()
                            st.session_state.llogaria = llogarite.hyr(u, fj)
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
        if st.button("👤 Vazhdo si vizitor (asgjë nuk ruhet)", width="stretch"):
            st.session_state.vizitor = True
            st.rerun()


try:
    pergatit_databazen()
except Exception as e:
    st.error(f"Nuk lidhem dot me Neo4j: {e}")
    st.stop()

llogaria = perdoruesi()
if not llogaria and not st.session_state.get("vizitor"):
    faqja_hyrjes()
    st.stop()

faqe_chat = st.Page(chat.faqja, title="Biseda", icon="💬", url_path="biseda", default=True)
if not llogaria:
    faqet = [faqe_chat]
elif llogaria["roli"] == "admin":
    faqet = {"FarmaBot": [faqe_chat, st.Page(profili.faqja, title="Llogaria ime", icon="👤", url_path="llogaria")],
             "Administrimi": [st.Page(admin.permbledhje, title="Përmbledhje", icon="📊", url_path="permbledhje"),
                              st.Page(admin.perdoruesit_faqe, title="Përdoruesit", icon="👥", url_path="perdoruesit"),
                              st.Page(admin.barnat_faqe, title="Ilaçet", icon="💊", url_path="barnat"),
                              st.Page(admin.backup_faqe, title="Backup", icon="💾", url_path="backup")]}
else:
    faqet = [faqe_chat, st.Page(profili.faqja, title="Llogaria ime", icon="👤", url_path="llogaria")]

with st.sidebar:
    emri = llogaria["perdoruesi"] if llogaria else "Vizitor"
    roli = ("🛡️ Admin" if llogaria["roli"] == "admin" else "👤 Përdorues") if llogaria else "pa llogari"
    st.markdown(f'<div class="fb-karte" style="padding:.7rem .9rem"><div class="fb-titull">{stili._e(emri)}</div>'
                f'<span class="fb-etikete">{roli}</span></div>', unsafe_allow_html=True)
    if st.button("🚪 Dil" if llogaria else "🔐 Hyr / Regjistrohu", width="stretch"):
        st.session_state.clear()
        st.rerun()

st.navigation(faqet).run()
