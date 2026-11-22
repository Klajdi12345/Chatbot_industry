"""Pamja e FarmaBot-it: CSS (temë e bardhë / e zezë, në stilin e Claude.ai), logo dhe kartat e ilaçeve
(HTML me tekst të escape-uar)."""
from html import escape

import streamlit as st

from config import ROOT

LOGO = str(ROOT / "assets" / "logo.png")
LOGO_ERRET = str(ROOT / "assets" / "logo_erret.png")
IKONA = str(ROOT / "assets" / "ikona.png")

# Ngjyrat e dy temave. Gjithçka tjetër në CSS i referon si var(--fb-...).
TEMAT = {
    "light": {
        "bg": "#faf9f5", "anesor": "#f3f1ea", "siperfaqe": "#ffffff", "siperfaqe2": "#efede5",
        "tekst": "#1f1e1d", "gri": "#6b6a64", "vije": "#e3e0d6", "hije": "rgba(31,30,29,.08)",
        "theks": "#0f8f74", "theks_lehte": "#e3f3ee", "theks_tekst": "#04694f",
        "kuq": "#dc2626", "kuq_lehte": "#fef2f2", "portokalli": "#b45309", "portokalli_lehte": "#fffbeb",
        "blu": "#1d4ed8", "blu_lehte": "#eff6ff",
    },
    "dark": {
        "bg": "#262624", "anesor": "#1f1e1d", "siperfaqe": "#30302e", "siperfaqe2": "#3a3a37",
        "tekst": "#f3f1ea", "gri": "#a8a59c", "vije": "#45443f", "hije": "rgba(0,0,0,.35)",
        "theks": "#3fc8a4", "theks_lehte": "#1f3a33", "theks_tekst": "#7ee0c3",
        "kuq": "#f87171", "kuq_lehte": "#3a2424", "portokalli": "#fbbf24", "portokalli_lehte": "#3a3122",
        "blu": "#93c5fd", "blu_lehte": "#1e2a3b",
    },
}

CSS = """
<style>
:root, .stApp { %(variablat)s color-scheme: %(skema)s; }

/* ---- baza ---- */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] { background: var(--fb-bg) !important; }
[data-testid="stHeader"] { box-shadow: none; }
.block-container { padding-top: 4.2rem; max-width: 1100px; }
.stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stMetricValue"], .stApp summary, .stApp [data-testid="stExpander"] summary p
{ color: var(--fb-tekst); }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p,
.stApp [data-testid="stMetricLabel"] p { color: var(--fb-gri) !important; }
.stApp h1, .stApp h2, .stApp h3 { font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  font-weight: 500; letter-spacing: -0.01em; }
.stApp a { color: var(--fb-theks); }
hr { border-color: var(--fb-vije) !important; }

/* ---- paneli anësor ---- */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div { background: var(--fb-anesor) !important; }
[data-testid="stSidebar"] { border-right: 1px solid var(--fb-vije); }
[data-testid="stSidebarNavLink"] span { color: var(--fb-tekst) !important; }
[data-testid="stSidebarNavLink"][aria-current="page"], [data-testid="stSidebarNavLink"]:hover
{ background: var(--fb-siperfaqe2) !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] details { background: transparent; border-color: var(--fb-vije); }

/* ---- fushat ---- */
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"], .stApp [data-baseweb="textarea"],
.stApp [data-baseweb="select"] > div, .stApp input, .stApp textarea
{ background: var(--fb-siperfaqe) !important; color: var(--fb-tekst) !important; border-color: var(--fb-vije) !important; }
.stApp input::placeholder, .stApp textarea::placeholder { color: var(--fb-gri) !important; opacity: 1; }
.stApp [data-baseweb="input"] button { background: var(--fb-siperfaqe) !important; color: var(--fb-tekst) !important; }
.stApp [data-testid="stNumberInput"] button { background: var(--fb-siperfaqe2) !important; color: var(--fb-tekst) !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="popover"] > div
{ background: var(--fb-siperfaqe) !important; color: var(--fb-tekst) !important; }
[data-baseweb="popover"] li:hover { background: var(--fb-siperfaqe2) !important; }

/* ---- butonat ---- */
.stApp button[kind="secondary"], .stApp button[kind="secondaryFormSubmit"], .stApp button[kind="segmented_control"],
.stApp [data-testid="stDownloadButton"] button
{ background: var(--fb-siperfaqe) !important; color: var(--fb-tekst) !important; border: 1px solid var(--fb-vije) !important;
  border-radius: 10px; font-weight: 600; }
.stApp button[kind="secondary"]:hover, .stApp button[kind="segmented_control"]:hover
{ border-color: var(--fb-theks) !important; color: var(--fb-theks) !important; }
.stApp button[kind="primary"], .stApp button[kind="primaryFormSubmit"], .stApp button[kind="segmented_controlActive"]
{ background: var(--fb-theks) !important; color: #fff !important; border: 1px solid var(--fb-theks) !important;
  border-radius: 10px; font-weight: 600; }
.stApp button[kind="tertiary"] { color: var(--fb-tekst) !important; font-size: 1.3rem; }
.stApp [data-testid="stButtonGroup"] button { background: var(--fb-siperfaqe) !important; color: var(--fb-tekst) !important;
  border-color: var(--fb-vije) !important; }
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"] { background: var(--fb-theks) !important; color: #fff !important;
  border-color: var(--fb-theks) !important; }
.stApp button p { color: inherit !important; }

/* ---- kontejnerët ---- */
.stApp [data-testid="stExpander"] details { background: var(--fb-siperfaqe); border: 1px solid var(--fb-vije); border-radius: 14px; }
.stApp [data-testid="stExpander"] summary { background: transparent !important; }
.stApp [data-testid="stExpander"] summary:hover p { color: var(--fb-theks); }
.stApp [data-testid="stExpander"] svg { color: var(--fb-gri); fill: currentColor; }
.stApp [data-testid="stForm"] { background: var(--fb-siperfaqe); border: 1px solid var(--fb-vije); border-radius: 18px;
  padding: 1.4rem; box-shadow: 0 10px 30px var(--fb-hije); }
.stApp [data-testid="stMetric"] { background: var(--fb-siperfaqe); border: 1px solid var(--fb-vije); border-radius: 14px; padding: .8rem 1rem; }
.stApp [data-baseweb="tab-list"] { background: transparent; }
.stApp [data-baseweb="tab"] p { color: var(--fb-gri); }
.stApp [data-baseweb="tab"][aria-selected="true"] p { color: var(--fb-theks); }
.stApp [data-baseweb="tab-highlight"] { background: var(--fb-theks) !important; }
.stApp [data-baseweb="tab-border"] { background: var(--fb-vije) !important; }

/* ---- biseda (si Claude.ai) ---- */
.fb-biseda .block-container, .block-container:has(.fb-biseda) { max-width: 800px; }
.stApp [data-testid="stChatMessage"] { background: transparent; border: none; padding: .4rem 0; gap: .8rem; }
.stApp [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: row-reverse; }
.stApp [data-testid="stChatMessageAvatarUser"] { display: none; }
.stApp [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"]
{ background: var(--fb-siperfaqe2); border-radius: 18px; padding: .65rem 1rem; max-width: 85%%; flex: 0 1 auto; margin-left: auto !important; margin-right: 0 !important; }
.stApp [data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p { font-size: 1.02rem; line-height: 1.6; }
.stApp [data-testid="stChatInput"] { background: var(--fb-siperfaqe) !important; border: 1px solid var(--fb-vije) !important;
  border-radius: 22px !important; box-shadow: 0 6px 24px var(--fb-hije); }
.stApp [data-testid="stChatInput"] > div, .stApp [data-testid="stChatInput"] [data-baseweb="textarea"],
.stApp [data-testid="stChatInput"] textarea { background: transparent !important; border: none !important; }
.stApp [data-testid="stChatInput"] textarea { font-size: 1rem; }
.stApp [data-testid="stChatInputSubmitButton"] { background: var(--fb-theks) !important; color: #fff !important; border-radius: 10px; }

.fb-pershendetje { text-align: center; margin: 9vh 0 1.4rem; }
.fb-pershendetje img { width: 46px; height: 46px; border-radius: 12px; vertical-align: middle; margin-right: .7rem; }
.fb-pershendetje span { font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif; font-size: 2.4rem;
  color: var(--fb-tekst); vertical-align: middle; }
.fb-pershendetje p { color: var(--fb-gri); margin-top: .6rem; font-size: .9rem; }

/* ---- hero i faqes së hyrjes ---- */
.fb-hero { background: linear-gradient(135deg, #10a37f 0%%, #0e4c92 100%%); border-radius: 24px;
  padding: 2.2rem 2rem; box-shadow: 0 20px 40px rgba(14,76,146,.25); }
.fb-hero, .fb-hero * { color: #fff !important; }
.fb-hero h1 { font-size: 2.3rem; margin: .6rem 0 .3rem; }
.fb-hero p { opacity: .9; font-size: 1.05rem; margin: 0 0 1.2rem; }
.fb-hero img { width: 64px; height: 64px; border-radius: 16px; box-shadow: 0 6px 16px rgba(0,0,0,.18); }
.fb-veti { display: flex; gap: .7rem; align-items: flex-start; background: rgba(255,255,255,.12);
  border-radius: 14px; padding: .7rem .9rem; margin-top: .6rem; }
.fb-veti b { display: block; } .fb-veti span { opacity: .85; font-size: .9rem; }
.fb-paralajmerim { margin-top: 1.2rem; font-size: .85rem; opacity: .85; }

/* ---- kartat e ilaçeve ---- */
.fb-karte { background: var(--fb-siperfaqe); border: 1px solid var(--fb-vije); border-radius: 16px;
  padding: 1rem 1.1rem; margin: .6rem 0; box-shadow: 0 4px 14px var(--fb-hije); }
.fb-koke { display: flex; gap: .8rem; align-items: center; }
.fb-pilula { width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center;
  background: var(--fb-theks_lehte); font-size: 1.3rem; flex-shrink: 0; }
.fb-titull { font-weight: 700; font-size: 1.05rem; color: var(--fb-tekst); }
.fb-nen { color: var(--fb-gri); font-size: .88rem; }
.fb-cipat { margin: .6rem 0 .2rem; display: flex; flex-wrap: wrap; gap: .35rem; }
.fb-cip { background: var(--fb-siperfaqe2); color: var(--fb-tekst); border-radius: 999px; padding: .15rem .6rem; font-size: .8rem; }
.fb-rrjete { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: .6rem; margin-top: .7rem; }
.fb-qeli { background: var(--fb-siperfaqe2); border-radius: 12px; padding: .55rem .7rem; }
.fb-qeli small { display: block; color: var(--fb-gri); font-size: .72rem; text-transform: uppercase;
  letter-spacing: .05em; font-weight: 700; margin-bottom: .15rem; }
.fb-qeli div { color: var(--fb-tekst); font-size: .9rem; line-height: 1.35; }
.fb-shenim { border-radius: 10px; padding: .5rem .7rem; margin-top: .55rem; font-size: .88rem; }
.fb-kujdes { background: var(--fb-portokalli_lehte); color: var(--fb-portokalli); }
.fb-femije { background: var(--fb-blu_lehte); color: var(--fb-blu); }
.fb-karte details { margin-top: .6rem; } .fb-karte summary { cursor: pointer; color: var(--fb-theks);
  font-weight: 600; font-size: .88rem; }
.fb-karte ul { margin: .4rem 0 0 1.1rem; padding: 0; color: var(--fb-tekst); font-size: .88rem; }
.fb-jo { border-left: 4px solid var(--fb-kuq); background: var(--fb-kuq_lehte); }
.fb-jo .fb-titull { color: var(--fb-kuq); }
.fb-alarm { border-left: 4px solid var(--fb-kuq); }
.fb-alarm .fb-titull, .fb-alarm summary.fb-titull { color: var(--fb-kuq) !important; }
.fb-etikete { display: inline-block; background: var(--fb-theks_lehte); color: var(--fb-theks_tekst); border-radius: 999px;
  padding: .1rem .55rem; font-size: .75rem; font-weight: 700; }
</style>
"""


def tema() -> str:
    return "dark" if st.session_state.get("tema") == "dark" else "light"


def apliko():
    emri = tema()
    variablat = " ".join(f"--fb-{k}: {v};" for k, v in TEMAT[emri].items())
    st.markdown(CSS % {"variablat": variablat, "skema": emri}, unsafe_allow_html=True)
    st.logo(LOGO_ERRET if emri == "dark" else LOGO, icon_image=IKONA, size="large")


def _e(x) -> str:
    return escape(str(x or ""))


ETIKETAT = {
    "sq": {"doza": "Doza (të rritur)", "maks": "Maksimumi", "kohe": "Kohëzgjatja", "si": "Si merret",
           "paral": "Paralajmërime dhe efekte anësore", "efekt": "Efekt anësor", "jo": "🚫 Nuk sugjerohen për ty",
           "alarm": "🩺 Kur duhet të shkosh te mjeku",
           "femije": "👶 Për fëmijët doza varet nga pesha dhe mosha. Përdor formën pediatrike dhe pyet farmacistin ose pediatrin."},
    "en": {"doza": "Dose (adults)", "maks": "Maximum", "kohe": "Duration", "si": "How to take",
           "paral": "Warnings and side effects", "efekt": "Side effect", "jo": "🚫 Not suggested for you",
           "alarm": "🩺 When to see a doctor",
           "femije": "👶 For children the dose depends on weight and age. Use the paediatric form and ask a pharmacist or paediatrician."},
}


def karta_ilaci(b: dict, pa_doza: bool, gjuha: str = "sq") -> str:
    E = ETIKETAT[gjuha]
    cipat = "".join(f'<span class="fb-cip">{_e(t)}</span>' for t in b.get("emra_tregtare") or [])
    if pa_doza:
        doza = f'<div class="fb-shenim fb-femije">{_e(E["femije"])}</div>'
    else:
        qelizat = [(E["doza"], b.get("doza")), (E["maks"], b.get("doza_maks")),
                   (E["kohe"], b.get("kohezgjatja")), (E["si"], b.get("si_merret"))]
        doza = '<div class="fb-rrjete">' + "".join(
            f'<div class="fb-qeli"><small>{_e(k)}</small><div>{_e(v)}</div></div>' for k, v in qelizat if v) + "</div>"
    kujdes = "".join(f'<div class="fb-shenim fb-kujdes">⚠️ <b>{_e(k["gjendje"])}:</b> {_e(k["arsye"])}</div>'
                     for k in b.get("kujdes_profili") or [])
    detaje = ""
    paral, efekte = b.get("paralajmerime") or [], b.get("efekte_anesore") or []
    if paral or efekte:
        detaje = (f"<details><summary>{_e(E['paral'])}</summary><ul>"
                  + "".join(f"<li>{_e(x)}</li>" for x in paral)
                  + "".join(f"<li>{_e(E['efekt'])}: {_e(x)}</li>" for x in efekte) + "</ul></details>")
    return (f'<div class="fb-karte"><div class="fb-koke"><div class="fb-pilula">💊</div><div>'
            f'<div class="fb-titull">{_e(b["emer"])}</div>'
            f'<div class="fb-nen">{_e(b.get("lende_aktive"))} · {_e(b.get("forma"))}</div></div></div>'
            f'<div class="fb-cipat">{cipat}</div>{doza}{kujdes}{detaje}</div>')


def karta_perjashtuara(lista: list[dict], gjuha: str = "sq") -> str:
    rreshta = "".join(f"<li><b>{_e(x['emer'])}</b>: {_e(' '.join(a['arsye'] for a in x['arsyet']))}</li>"
                      for x in lista)
    return (f'<div class="fb-karte fb-jo"><div class="fb-titull">{_e(ETIKETAT[gjuha]["jo"])}</div>'
            f'<ul>{rreshta}</ul></div>')


def karta_alarmi(simptomat: list[dict], gjuha: str = "sq") -> str:
    pjeset = "".join(f"<li><b>{_e(s['emer'])}:</b> {_e(a)}</li>" for s in simptomat for a in s["shenja_alarmi"])
    return (f'<div class="fb-karte fb-alarm"><details><summary class="fb-titull">'
            f'{_e(ETIKETAT[gjuha]["alarm"])}</summary><ul>{pjeset}</ul></details></div>')
