"""Gjëra që i përdorin disa faqe."""
import streamlit as st

from chatbot import Pergjigje
from config import query
from perkthimi import perkthe_shume
from faqet.stili import karta_alarmi, karta_ilaci, karta_perjashtuara

AUTOMATIKE = {"femije_nen_12", "nen_16", "mbi_65"}  # llogariten nga mosha


@st.cache_data(ttl=3600)
def gjendjet_nga_db() -> dict[str, str]:
    rows = query("MATCH (g:Gjendje) RETURN g.id AS id, g.emer AS emer ORDER BY g.emer")
    return {r["id"]: r["emer"] for r in rows}


def vendos_me_vone(**vlerat):
    """Widget-et nuk ndryshohen dot pasi janë vizatuar: ruaji për rrotullimin e ardhshëm."""
    st.session_state.setdefault("_ne_pritje", {}).update(vlerat)


def apliko_ne_pritje():
    for k, v in st.session_state.pop("_ne_pritje", {}).items():
        st.session_state[k] = v


def perdoruesi() -> dict | None:
    """{perdoruesi, roli, person_id} ose None për përdorim anonim."""
    return st.session_state.get("llogaria")


FUSHAT_E_ILACIT = ("emer", "lende_aktive", "forma", "doza", "doza_maks", "kohezgjatja", "si_merret")


def _ne_anglisht(p: Pergjigje) -> tuple[list, list, list]:
    """Kopje të kartave me fushat e përkthyera (cache te data/perkthime_en.json; numrat kontrollohen).
    Emrat tregtarë nuk përkthehen."""
    tekste = []
    for b in p.barnat:
        tekste += [b.get(k) or "" for k in FUSHAT_E_ILACIT] + list(b.get("paralajmerime") or []) + \
                  list(b.get("efekte_anesore") or []) + [x for k in b.get("kujdes_profili") or [] for x in (k["gjendje"], k["arsye"])]
    for x in p.te_perjashtuara:
        tekste += [x["emer"]] + [a["arsye"] for a in x["arsyet"]]
    for s in p.simptomat:
        tekste += [s["emer"]] + list(s["shenja_alarmi"])
    fjalori = dict(zip(tekste, perkthe_shume(tekste)))
    t = lambda x: fjalori.get(x, x) if x else x  # noqa: E731
    barnat = [{**b, **{k: t(b.get(k)) for k in FUSHAT_E_ILACIT},
               "paralajmerime": [t(x) for x in b.get("paralajmerime") or []],
               "efekte_anesore": [t(x) for x in b.get("efekte_anesore") or []],
               "kujdes_profili": [{"gjendje": t(k["gjendje"]), "arsye": t(k["arsye"])} for k in b.get("kujdes_profili") or []]}
              for b in p.barnat]
    perjashtuara = [{"emer": t(x["emer"]), "arsyet": [{**a, "arsye": t(a["arsye"])} for a in x["arsyet"]]}
                    for x in p.te_perjashtuara]
    simptomat = [{**s, "emer": t(s["emer"]), "shenja_alarmi": [t(a) for a in s["shenja_alarmi"]]} for s in p.simptomat]
    return barnat, perjashtuara, simptomat


def _emri_burimit(d: dict) -> str:
    return f"{d['burimi']} f.{d['faqja']}" if d.get("faqja") else d["burimi"]


def shfaq_kartat(p: Pergjigje):
    if p.urgjence:
        return
    gjuha = getattr(p, "gjuha", "sq")
    barnat, perjashtuara, simptomat = (_ne_anglisht(p) if gjuha == "en"
                                       else (p.barnat, p.te_perjashtuara, p.simptomat))
    html = "".join(karta_ilaci(b, p.pa_doza, gjuha) for b in barnat)
    if perjashtuara:
        html += karta_perjashtuara(perjashtuara, gjuha)
    if simptomat:
        html += karta_alarmi(simptomat, gjuha)
    if html:
        st.markdown(html, unsafe_allow_html=True)
    _shfaq_fleteudhezuesit(p, gjuha)
    if p.burime:
        lidhjet = {}
        for d in p.burime:
            lidhjet.setdefault(_emri_burimit(d), d.get("url"))
        st.caption(("📄 Sources: " if gjuha == "en" else "📄 Burime: ")
                   + ", ".join(f"[{e}]({u})" if u else e for e, u in sorted(lidhjet.items())))


def _shfaq_fleteudhezuesit(p: Pergjigje, gjuha: str):
    """Teksti zyrtar i FDA-së (anglisht, pa përkthim) për ilaçet e sugjeruara: personi e lexon vetë."""
    from ngarko_burimet import TITUJT_E_SEKSIONEVE
    sipas_ilacit = {}
    for d in getattr(p, "fleteudhezuesit", None) or []:
        sipas_ilacit.setdefault(d["emer"], []).append(d)
    for emer, pjeset in sipas_ilacit.items():
        titulli = (f"📄 Official FDA leaflet: {emer}" if gjuha == "en"
                   else f"📄 Fletëudhëzuesi zyrtar FDA: {emer} (anglisht)")
        with st.expander(titulli):
            for d in pjeset:
                st.markdown(f"**{TITUJT_E_SEKSIONEVE.get(d['seksioni'], d['seksioni'])}**")
                st.caption(d["tekst"].split(": ", 1)[-1][:1200])
            if pjeset[0].get("url"):
                st.markdown(f"[DailyMed]({pjeset[0]['url']})")
