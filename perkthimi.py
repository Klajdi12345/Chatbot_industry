"""Përkthimi shqip → anglisht i përgjigjeve, kur personi shkruan në anglisht.

Logjika e FarmaBot-it punon në shqip (rregullat, databaza, dozat). Kur mesazhi është në anglisht,
përgjigjja e gatshme përkthehet me modelin gjuhësor, me tre masa sigurie:
  * çdo numër i tekstit shqip (doza, orë, ditë, 127/112) duhet të jetë edhe te përkthimi,
    përndryshe përkthimi refuzohet dhe shfaqet origjinali shqip me një shënim në anglisht;
  * emrat e ilaçeve, markdown-i dhe emoji-t ruhen;
  * përkthimet ruhen te data/perkthime_en.json (cache), që teksti i njëjtë të mos përkthehet dy herë
    dhe të mund të kontrollohet nga një njeri.
"""
import json
import re
import threading
from functools import lru_cache

from config import LLM_MODEL, OLLAMA_URL, ROOT

import requests

CACHE = ROOT / "data" / "perkthime_en.json"
_bllok = threading.Lock()

PROMPT = """You translate the replies of FarmaBot, an Albanian pharmacy assistant, from Albanian into clear, natural English.
Rules:
- Translate everything; output ONLY the translation, nothing else.
- Keep the Markdown formatting, line breaks, bullet points, bold/italics and emojis exactly.
- Keep every number, dose, unit and phone number exactly as written (e.g. "500 mg", "4 g", "127", "112").
- Keep medicine and brand names unchanged (e.g. Paracetamol, Panadol, Ibuprofen, Brufen).
- "farmacist" = pharmacist, "mjek" = doctor, "fletëudhëzues" = package leaflet, "pa recetë" = over the counter."""

SHENIM_DESHTIMI = ("_(I could not verify an exact English translation of this answer, so here is the original "
                   "Albanian text. Please ask a pharmacist to explain the doses.)_\n\n")


@lru_cache
def _cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def _ruaj():
    with _bllok:
        CACHE.write_text(json.dumps(_cache(), ensure_ascii=False, indent=1), encoding="utf-8")


def _numrat(tekst: str) -> list[str]:
    return sorted(re.sub(r"(?<=\d),(?=\d)", ".", n) for n in re.findall(r"\d+(?:[.,]\d+)?", tekst))


def numrat_perputhen(origjinali: str, perkthimi: str) -> bool:
    """Çdo numër i origjinalit duhet të jetë te përkthimi (përkthimi mund të ketë më shumë, jo më pak)."""
    mbetet = list(_numrat(perkthimi))
    for n in _numrat(origjinali):
        if n not in mbetet:
            return False
        mbetet.remove(n)
    return True


def _thirr_modelin(tekst: str, terma: dict | None = None) -> str:
    sistemi = PROMPT
    if terma:
        prezente = {sq: en for sq, en in terma.items() if sq.lower() in tekst.lower()}
        if prezente:
            sistemi += ("\n- GLOSSARY (mandatory, use these exact English terms):\n"
                        + "\n".join(f"  {sq} = {en}" for sq, en in prezente.items()))
    r = requests.post(f"{OLLAMA_URL}/api/chat", json={
        "model": LLM_MODEL, "stream": False, "keep_alive": "30m",
        "messages": [{"role": "system", "content": sistemi}, {"role": "user", "content": tekst}],
        "options": {"temperature": 0.1, "num_ctx": 8192, "num_predict": 1500},
    }, timeout=600)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def perkthe(tekst: str, cache: bool = True, terma: dict | None = None) -> tuple[str, bool]:
    """(teksti anglisht, a u përkthye me sukses). Në dështim kthen origjinalin me shënim."""
    tekst = (tekst or "").strip()
    if not tekst:
        return tekst, True
    if cache and tekst in _cache():
        return _cache()[tekst], True
    for _ in range(2):  # një provë e dytë nëse numrat nuk përputhen
        try:
            en = _thirr_modelin(tekst, terma)
        except requests.RequestException:
            break
        if en and numrat_perputhen(tekst, en):
            if cache:
                _cache()[tekst] = en
                _ruaj()
            return en, True
    return SHENIM_DESHTIMI + tekst, False


def perkthe_fushen(tekst: str) -> str:
    """Për kartat: tekst i shkurtër nga databaza. Nëse s'përkthehet dot saktë, mbetet shqip."""
    en, ok = perkthe(tekst)
    return en if ok else tekst


def perkthe_shume(tekste: list[str], madhesia: int = 25) -> list[str]:
    """Përkthen shumë tekste të shkurtra (fushat e kartave) me pak thirrje. Ato që nuk kalojnë kontrollin
    e numrave mbeten shqip. Rezultati ka të njëjtën renditje si hyrja."""
    c = _cache()
    mungojne = [t for t in dict.fromkeys(x.strip() for x in tekste if x and x.strip()) if t not in c]
    for i in range(0, len(mungojne), madhesia):
        grupi = mungojne[i:i + madhesia]
        hyrja = json.dumps(grupi, ensure_ascii=False)
        sistemi = (PROMPT + "\n- Input is a JSON list of Albanian strings. "
                   'Return JSON {"en": [...]} with exactly one English translation per item, same order.')
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", json={
                "model": LLM_MODEL, "stream": False, "format": "json", "keep_alive": "30m",
                "messages": [{"role": "system", "content": sistemi}, {"role": "user", "content": hyrja}],
                "options": {"temperature": 0.1, "num_ctx": 8192, "num_predict": 4096}}, timeout=900)
            r.raise_for_status()
            dalja = json.loads(r.json()["message"]["content"]).get("en") or []
        except Exception:
            continue
        if len(dalja) != len(grupi):
            continue
        for sq, en in zip(grupi, dalja):
            if isinstance(en, str) and en.strip() and numrat_perputhen(sq, en):
                c[sq] = en.strip()
        _ruaj()
    return [c.get((t or "").strip(), t) for t in tekste]
