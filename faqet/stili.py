"""Pamja e FarmaBot-it: CSS, logo dhe kartat e ilaçeve (HTML me tekst të escape-uar)."""
from html import escape

import streamlit as st

from config import ROOT

LOGO = str(ROOT / "assets" / "logo.png")
IKONA = str(ROOT / "assets" / "ikona.png")

CSS = """
<style>
:root {
  --fb-jeshile: #10a37f; --fb-jeshile-erret: #0e7490; --fb-jeshile-lehte: #e7f7f2;
  --fb-tekst: #0f172a; --fb-gri: #64748b; --fb-vije: #e2e8f0; --fb-karte: #ffffff;
  --fb-kuq: #dc2626; --fb-kuq-lehte: #fef2f2; --fb-portokalli: #b45309; --fb-portokalli-lehte: #fffbeb;
}
.block-container { padding-top: 2rem; max-width: 1100px; }
h1, h2, h3 { letter-spacing: -0.02em; }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--fb-vije); }
[data-testid="stChatMessage"] { background: var(--fb-karte); border: 1px solid var(--fb-vije);
  border-radius: 16px; padding: 0.9rem 1rem; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
[data-testid="stForm"] { background: var(--fb-karte); border: 1px solid var(--fb-vije); border-radius: 18px;
  padding: 1.4rem; box-shadow: 0 10px 30px rgba(15,23,42,.06); }
[data-testid="stMetric"] { background: var(--fb-karte); border: 1px solid var(--fb-vije); border-radius: 14px;
  padding: .8rem 1rem; }
.stButton button, .stFormSubmitButton button { border-radius: 10px; font-weight: 600; }

/* ---- hero i faqes së hyrjes ---- */
.fb-hero { background: linear-gradient(135deg, #10a37f 0%, #0e7490 100%); color: #fff; border-radius: 24px;
  padding: 2.2rem 2rem; box-shadow: 0 20px 40px rgba(14,116,144,.25); }
.fb-hero h1 { color: #fff; font-size: 2.3rem; margin: .6rem 0 .3rem; }
.fb-hero p { color: rgba(255,255,255,.9); font-size: 1.05rem; margin: 0 0 1.2rem; }
.fb-hero img { width: 64px; height: 64px; border-radius: 16px; box-shadow: 0 6px 16px rgba(0,0,0,.18); }
.fb-veti { display: flex; gap: .7rem; align-items: flex-start; background: rgba(255,255,255,.12);
  border-radius: 14px; padding: .7rem .9rem; margin-top: .6rem; }
.fb-veti b { display: block; color: #fff; } .fb-veti span { color: rgba(255,255,255,.85); font-size: .9rem; }
.fb-paralajmerim { margin-top: 1.2rem; font-size: .85rem; color: rgba(255,255,255,.85); }

/* ---- kartat e ilaçeve ---- */
.fb-karte { background: var(--fb-karte); border: 1px solid var(--fb-vije); border-radius: 16px;
  padding: 1rem 1.1rem; margin: .6rem 0; box-shadow: 0 4px 14px rgba(15,23,42,.05); }
.fb-koke { display: flex; gap: .8rem; align-items: center; }
.fb-pilula { width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center;
  background: var(--fb-jeshile-lehte); font-size: 1.3rem; flex-shrink: 0; }
.fb-titull { font-weight: 700; font-size: 1.05rem; color: var(--fb-tekst); }
.fb-nen { color: var(--fb-gri); font-size: .88rem; }
.fb-cipat { margin: .6rem 0 .2rem; display: flex; flex-wrap: wrap; gap: .35rem; }
.fb-cip { background: #f1f5f9; color: #334155; border-radius: 999px; padding: .15rem .6rem; font-size: .8rem; }
.fb-rrjete { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: .6rem; margin-top: .7rem; }
.fb-qeli { background: #f8fafc; border-radius: 12px; padding: .55rem .7rem; }
.fb-qeli small { display: block; color: var(--fb-gri); font-size: .72rem; text-transform: uppercase;
  letter-spacing: .05em; font-weight: 700; margin-bottom: .15rem; }
.fb-qeli div { color: var(--fb-tekst); font-size: .9rem; line-height: 1.35; }
.fb-shenim { border-radius: 10px; padding: .5rem .7rem; margin-top: .55rem; font-size: .88rem; }
.fb-kujdes { background: var(--fb-portokalli-lehte); color: var(--fb-portokalli); }
.fb-femije { background: #eff6ff; color: #1d4ed8; }
.fb-karte details { margin-top: .6rem; } .fb-karte summary { cursor: pointer; color: var(--fb-jeshile-erret);
  font-weight: 600; font-size: .88rem; }
.fb-karte ul { margin: .4rem 0 0 1.1rem; padding: 0; color: #334155; font-size: .88rem; }
.fb-jo { border-left: 4px solid var(--fb-kuq); background: var(--fb-kuq-lehte); }
.fb-jo .fb-titull { color: var(--fb-kuq); }
.fb-alarm { border-left: 4px solid var(--fb-kuq); }
.fb-alarm .fb-titull { color: var(--fb-kuq); }
.fb-motor { display: inline-flex; align-items: center; gap: .35rem; vertical-align: middle; margin-left: .5rem;
  font-size: .78rem; font-weight: 700; letter-spacing: 0; border-radius: 999px; padding: .2rem .7rem;
  border: 1px solid var(--fb-vije); background: #fff; color: #334155; }
.fb-motor.claude { background: linear-gradient(135deg, #fff7ed, #fdf2f8); border-color: #fed7aa; color: #9a3412; }
.fb-motor .pika { width: 8px; height: 8px; border-radius: 50%; background: #10a37f; box-shadow: 0 0 0 3px rgba(16,163,127,.15); }
.fb-motor.claude .pika { background: #d97757; box-shadow: 0 0 0 3px rgba(217,119,87,.18); }
[data-testid="stChatInput"] textarea { font-size: 1rem; }
[data-testid="stChatInput"] > div { border-radius: 18px !important; box-shadow: 0 8px 24px rgba(15,23,42,.08); }
[data-testid="stExpander"] details { border-radius: 14px; }
.fb-etikete { display: inline-block; background: var(--fb-jeshile-lehte); color: #047857; border-radius: 999px;
  padding: .1rem .55rem; font-size: .75rem; font-weight: 700; }
</style>
"""


def stili_motorit(emri: str, motori: str) -> str:
    """Etiketa e vogël pranë titullit që tregon cili motor AI po përgjigjet."""
    return f'<span class="fb-motor {_e(motori)}"><span class="pika"></span>{_e(emri)}</span>'


def apliko():
    st.markdown(CSS, unsafe_allow_html=True)
    st.logo(LOGO, icon_image=IKONA, size="large")


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
    return (f'<div class="fb-karte fb-alarm"><details><summary class="fb-titull" style="color:#dc2626">'
            f'{_e(ETIKETAT[gjuha]["alarm"])}</summary><ul>{pjeset}</ul></details></div>')
