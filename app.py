"""FarmaBot: hyrja, rolet dhe navigimi.   Nis me:  streamlit run app.py

Rolet:
  * vizitor (pa llogari) → vetëm biseda, asgjë nuk ruhet
  * përdorues           → biseda + llogaria ime (profili dhe historia ruhen në Neo4j)
  * admin               → gjithçka + përmbledhje, përdoruesit, ilaçet, backup

Sipër çdo faqeje: ☰ hap/mbyll panelin anësor · SQ/EN gjuha · ☀️/🌙 tema.
Gjuha dhe tema ruhen në URL (?gjuha=en&tema=dark), prandaj mbeten edhe pas rifreskimit të faqes.
"""
import streamlit as st

import llogarite
import perdoruesit as db_p
from faqet import admin, chat, profili
from faqet import stili
from faqet.perbashket import perdoruesi
from faqet.teksti import t

st.session_state.setdefault("paneli_hapur", True)
st.set_page_config(page_title="FarmaBot", page_icon=stili.IKONA, layout="wide",
                   initial_sidebar_state="expanded" if st.session_state.paneli_hapur else "collapsed")


def _nderro_panelin():
    st.session_state.paneli_hapur = not st.session_state.paneli_hapur


ZGJEDHJET = {"gjuha": (("sq", "en"), "sq"), "tema": (("light", "dark"), "light")}


def _nga_url():
    """Gjuha dhe tema lexohen nga URL-ja (?gjuha=en&tema=dark) herën e parë në sesion."""
    for celesi, (lejuar, parazgjedhur) in ZGJEDHJET.items():
        if st.session_state.get(celesi) not in lejuar:
            v = st.query_params.get(celesi)
            st.session_state[celesi] = v if v in lejuar else parazgjedhur


def _ne_url(celesi: str):
    """Ruaj zgjedhjen në URL, që të mbetet edhe pas rifreskimit të faqes."""
    v, parazgjedhur = st.session_state.get(celesi), ZGJEDHJET[celesi][1]
    if v == parazgjedhur:
        st.query_params.pop(celesi, None)
    else:
        st.query_params[celesi] = v


def shiriti_siper():
    """☰ për panelin anësor, gjuha dhe tema: në krye të çdo faqeje."""
    _nga_url()
    k1, _, k2, k3 = st.columns([0.5, 3.2, 1.6, 3.2], vertical_alignment="center")
    k1.button("☰", key="btn_paneli", on_click=_nderro_panelin, help=t("paneli"), type="tertiary")
    k2.segmented_control(t("gjuha"), ["sq", "en"], format_func={"sq": "SQ", "en": "EN"}.get,
                         required=True, key="gjuha", on_change=_ne_url, args=("gjuha",),
                         label_visibility="collapsed")
    k3.segmented_control(t("tema"), ["light", "dark"],
                         format_func=lambda x: t("e_bardhe") if x == "light" else t("e_zeze"),
                         required=True, key="tema", on_change=_ne_url, args=("tema",),
                         label_visibility="collapsed")


shiriti_siper()
stili.apliko()


@st.cache_resource
def pergatit_databazen():
    db_p.krijo_skemen()
    return llogarite.sigurohu_per_admin()  # fjalëkalimi vetëm herën e parë (ruhet te .env)


def _rifillo_sesionin():
    """Pas hyrjes/daljes pastrohet sesioni, por ruhen zgjedhjet e pamjes."""
    ruaj = {k: st.session_state[k] for k in ("paneli_hapur", "gjuha", "tema") if k in st.session_state}
    st.session_state.clear()
    st.session_state.update(ruaj)


def _hero() -> str:
    import base64
    ikona = base64.b64encode(open(stili.IKONA, "rb").read()).decode()
    veti = [("🩺", t("veti1_t"), t("veti1_d")), ("🛡️", t("veti2_t"), t("veti2_d")), ("🚑", t("veti3_t"), t("veti3_d"))]
    rreshta = "".join(f'<div class="fb-veti"><div style="font-size:1.4rem">{i}</div><div><b>{tt}</b>'
                      f'<span>{d}</span></div></div>' for i, tt, d in veti)
    return (f'<div class="fb-hero"><img src="data:image/png;base64,{ikona}" alt="FarmaBot">'
            f'<h1>FarmaBot</h1><p>{t("hero_nen")}</p>{rreshta}'
            f'<div class="fb-paralajmerim">{t("paralajmerim")}</div></div>')


def faqja_hyrjes():
    majtas, djathtas = st.columns([1.1, 1], gap="large")
    with majtas:
        st.markdown(_hero(), unsafe_allow_html=True)
    with djathtas:
        st.markdown(f"### {t('mire_se_erdhe')}")
        st.caption(t("hyr_shpjegim"))
        hyr, regj = st.tabs([t("hyr"), t("regjistrohu")])
        with hyr:
            with st.form("hyrja"):
                u = st.text_input(t("perdoruesi"))
                fj = st.text_input(t("fjalekalimi"), type="password")
                if st.form_submit_button(t("hyr_btn"), type="primary", width="stretch"):
                    llogaria = llogarite.hyr(u, fj)
                    if llogaria:
                        _rifillo_sesionin()
                        st.session_state.llogaria = llogaria
                        st.rerun()
                    st.error(t("gabim_hyrje"))
        with regj:
            with st.form("regjistrimi"):
                u = st.text_input(t("perdoruesi"), placeholder="p.sh. ëndrra_çela ose john.smith",
                                  help=t("perdoruesi_help"))
                emer = st.text_input(t("emri_yt"), placeholder="p.sh. Arbëreshë Çela", help=t("emri_help"))
                mosha = st.number_input(t("mosha"), min_value=0, max_value=110, value=None, step=1)
                fj = st.text_input(t("fjalekalimi_min"), type="password")
                fj2 = st.text_input(t("perserit"), type="password")
                pelqim = st.checkbox(t("pelqim"))
                st.caption(t("shkronjat"))
                if st.form_submit_button(t("krijo"), width="stretch"):
                    gabim = llogarite.valido(u, fj) or llogarite.valido_emrin(emer)
                    if gabim:
                        st.error(gabim)
                    elif fj != fj2:
                        st.error(t("nuk_perputhen"))
                    elif not pelqim:
                        st.error(t("duhet_pelqimi"))
                    else:
                        try:
                            llogarite.krijo_llogari(u, fj, "perdorues", emer or None,
                                                    int(mosha) if mosha is not None else None)
                            _rifillo_sesionin()
                            st.session_state.llogaria = llogarite.hyr(u, fj)
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
        if st.button(t("vizitor_btn"), width="stretch"):
            st.session_state.vizitor = True
            st.rerun()


try:
    pergatit_databazen()
except Exception as e:
    st.error(f"{t('gabim_neo4j')}: {e}")
    st.stop()

llogaria = perdoruesi()
if not llogaria and not st.session_state.get("vizitor"):
    faqja_hyrjes()
    st.stop()

faqe_chat = st.Page(chat.faqja, title=t("biseda"), icon="💬", url_path="biseda", default=True)
faqe_llogaria = st.Page(profili.faqja, title=t("llogaria_ime"), icon="👤", url_path="llogaria")
if not llogaria:
    faqet = [faqe_chat]
elif llogaria["roli"] == "admin":
    faqet = {"FarmaBot": [faqe_chat, faqe_llogaria],
             t("administrimi"): [st.Page(admin.permbledhje, title=t("permbledhje"), icon="📊", url_path="permbledhje"),
                                 st.Page(admin.perdoruesit_faqe, title=t("perdoruesit"), icon="👥", url_path="perdoruesit"),
                                 st.Page(admin.barnat_faqe, title=t("ilacet"), icon="💊", url_path="barnat"),
                                 st.Page(admin.backup_faqe, title=t("backup"), icon="💾", url_path="backup")]}
else:
    faqet = [faqe_chat, faqe_llogaria]

with st.sidebar:
    emri = llogaria["perdoruesi"] if llogaria else t("vizitor")
    roli = (t("admin") if llogaria["roli"] == "admin" else t("perdorues")) if llogaria else t("pa_llogari")
    st.markdown(f'<div class="fb-karte" style="padding:.7rem .9rem"><div class="fb-titull">{stili._e(emri)}</div>'
                f'<span class="fb-etikete">{roli}</span></div>', unsafe_allow_html=True)
    if st.button(t("dil") if llogaria else t("hyr_regj"), width="stretch"):
        _rifillo_sesionin()
        st.rerun()

st.navigation(faqet).run()
