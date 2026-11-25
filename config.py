"""Konfigurimi i përbashkët: lidhja me Neo4j dhe modelet e Ollama-s."""
import logging
import os
import unicodedata
from functools import lru_cache
from pathlib import Path

import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")  # jo "localhost": në Windows humb ~2 s me IPv6
LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")
EMBED_DIM = 1024  # bge-m3
DATABASE = os.getenv("NEO4J_DATABASE") or None

INDEKSI_FRAZAVE = "fraze_embedding"
INDEKSI_PDF = "chunk_embedding"


# Dy mënyra lidhjeje me të njëjtën databazë Neo4j Aura:
#   NEO4J_TRANSPORT=bolt   → drajveri klasik neo4j+s:// në portin 7687 (më i shpejtë)
#   NEO4J_TRANSPORT=https  → Query API përmes portit 443 (punon edhe kur rrjeti bllokon 7687)
#   NEO4J_TRANSPORT=auto   → provon Bolt; nëse rrjeti e bllokon, kalon vetë në HTTPS (parazgjedhja)
TRANSPORT = os.getenv("NEO4J_TRANSPORT", "auto").lower()
BOLT_TIMEOUT = 10  # sekonda për provën e Bolt-it në modalitetin auto
_AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
_session = requests.Session()


def _uri() -> str:
    uri = os.getenv("NEO4J_URI")
    if not uri:
        raise RuntimeError("NEO4J_URI mungon te skedari .env")
    return uri


@lru_cache
def get_driver():
    return GraphDatabase.driver(_uri(), auth=_AUTH, connection_timeout=20,
                                notifications_min_severity="OFF")


def _query_https(cypher: str, params: dict) -> list[dict]:
    host = _uri().split("://", 1)[1].split("/")[0].split(":")[0]
    r = _session.post(f"https://{host}/db/{DATABASE or 'neo4j'}/query/v2", auth=_AUTH,
                      json={"statement": cypher, "parameters": params}, timeout=120)
    try:
        body = r.json()
    except ValueError:
        r.raise_for_status()
        raise
    if body.get("errors"):
        e = body["errors"][0]
        raise RuntimeError(f"Neo4j: {e.get('code')}: {e.get('message')}")
    r.raise_for_status()
    fields = body["data"]["fields"]
    return [dict(zip(fields, row)) for row in body["data"]["values"]]


def _bolt_punon() -> bool:
    """Provon Bolt-in me afat kohor (drajveri vetë mund të presë shumë kur porti bllokohet)."""
    import threading
    rezultat = {}

    def prova():
        try:
            get_driver().verify_connectivity()
            rezultat["ok"] = True
        except Exception as e:
            rezultat["gabim"] = e

    t = threading.Thread(target=prova, daemon=True)
    t.start()
    t.join(BOLT_TIMEOUT)
    return rezultat.get("ok", False)


@lru_cache
def menyra_lidhjes() -> str:
    """Kthen 'bolt' ose 'https' sipas NEO4J_TRANSPORT (vendoset një herë për proces)."""
    if TRANSPORT in ("bolt", "https"):
        return TRANSPORT
    return "bolt" if _bolt_punon() else "https"


def query(cypher: str, **params) -> list[dict]:
    """Ekzekuton një query Cypher dhe kthen listë me dict (njësoj për të dyja mënyrat)."""
    if menyra_lidhjes() == "bolt":
        records, _, _ = get_driver().execute_query(cypher, params, database_=DATABASE)
        return [r.data() for r in records]
    return _query_https(cypher, params)


def kontrollo_lidhjen() -> str:
    query("RETURN 1 AS ok")
    return menyra_lidhjes()


def embed(tekste: list[str]) -> list[list[float]]:
    """Embeddings me bge-m3 përmes API-së së Ollama-s."""
    r = requests.post(f"{OLLAMA_URL}/api/embed",
                      json={"model": EMBED_MODEL, "input": tekste}, timeout=300)
    r.raise_for_status()
    return r.json()["embeddings"]


# ---------------------------------------------------------------- modeli rezervë
# Nëse modeli kryesor dështon (s'ngarkohet, mbaron memoria, s'përgjigjet në kohë), përgjigjen e jep
# llama3.2:3b: më i vogël dhe më i shpejtë. Shqipja e tij është më e dobët, por është më mirë se asnjë përgjigje.
REZERVE_MODEL = os.getenv("OLLAMA_REZERVE_MODEL", "llama3.2:3b")
KOHA_KRYESORI = int(os.getenv("OLLAMA_KOHA_KRYESORI", "180"))  # sekonda para se të kalohet te rezerva
log = logging.getLogger("farmabot.modelet")
MODELI_I_FUNDIT = {"modeli": None, "rezerve": False}   # cili model u përdor herën e fundit (për teste/log)


def modelet_per_rradhe(kryesori: str) -> list[str]:
    """[kryesori, rezerva]: rezerva shtohet vetëm nëse është e ndryshme dhe e instaluar."""
    lista = [kryesori]
    if REZERVE_MODEL and REZERVE_MODEL != kryesori and _aftesite(REZERVE_MODEL):
        lista.append(REZERVE_MODEL)
    return lista


def chat_me_rezerve(trupi: dict, kryesori: str = None, timeout: int = 600, rezerve: bool = True) -> str:
    """Thirrje /api/chat pa streaming: provon modelin kryesor, pastaj (nëse rezerve=True) modelin rezervë."""
    kryesori = kryesori or LLM_MODEL
    modelet = modelet_per_rradhe(kryesori) if rezerve else [kryesori]
    gabimi = None
    for i, model in enumerate(modelet):
        try:
            koha = min(timeout, KOHA_KRYESORI) if i < len(modelet) - 1 else timeout
            r = requests.post(f"{OLLAMA_URL}/api/chat", json={**trupi, "model": model}, timeout=koha)
            r.raise_for_status()
            tekst = r.json()["message"]["content"].strip()
            if not tekst:
                raise ValueError("përgjigje bosh")
            MODELI_I_FUNDIT.update(modeli=model, rezerve=i > 0)
            if i > 0:
                log.warning("U përdor modeli rezervë %s (kryesori %s dështoi: %s)", model, kryesori, gabimi)
            return tekst
        except (requests.RequestException, ValueError, KeyError) as e:
            gabimi = e
            log.warning("Modeli %s dështoi: %s", model, e)
    raise gabimi


def chat(mesazhet: list[dict]) -> str:
    """mesazhet: [{'role': 'system'|'user'|'assistant', 'content': ...}]"""
    return chat_me_rezerve({"messages": mesazhet, "stream": False,
                            "options": {"temperature": 0.5, "num_ctx": 4096}, "keep_alive": "30m"})


# ---------------------------------------------------------------- modeli që "mendon"
# Modaliteti "mendim i thellë": modeli arsyeton (thinking) para se të përgjigjet, si Claude.
# qwen3 / deepseek-r1 / gpt-oss kanë thinking në Ollama; nëse modeli s'është i instaluar, përdoret LLM_MODEL.
THINK_MODEL = os.getenv("OLLAMA_THINK_MODEL", "qwen3:8b")


@lru_cache
def _aftesite(model: str) -> tuple[str, ...]:
    try:
        r = requests.post(f"{OLLAMA_URL}/api/show", json={"model": model}, timeout=10)
        if r.status_code != 200:
            return ()
        return tuple(r.json().get("capabilities") or ("completion",))
    except requests.RequestException:
        return ()


def modeli_i_mendimit() -> tuple[str, bool]:
    """(modeli, a mendon) për modalitetin e thellë."""
    if "thinking" in _aftesite(THINK_MODEL):
        return THINK_MODEL, True
    return LLM_MODEL, "thinking" in _aftesite(LLM_MODEL)


def chat_mendo(mesazhet: list[dict], on_mendim=None, on_pergjigje=None, format_json: bool = False,
               num_predict: int = 2048, temperatura: float = 0.4) -> tuple[str, str]:
    """Si chat(), por me modelin që mendon dhe me streaming.
    on_mendim(copa) thirret për çdo copë të arsyetimit, on_pergjigje(copa) për përgjigjen.
    Kthen (pergjigja, mendimi)."""
    import json as _json
    model, mendon = modeli_i_mendimit()
    # Radha: modeli që mendon → modeli kryesor → modeli rezervë (pa dyfishime, vetëm të instaluarit).
    radha = [(model, mendon)]
    for m in modelet_per_rradhe(LLM_MODEL):
        if m not in [x for x, _ in radha]:
            radha.append((m, "thinking" in _aftesite(m)))
    gabimi = None
    for i, (model, mendon) in enumerate(radha):
        trupi = {"model": model, "messages": mesazhet, "stream": True, "keep_alive": "30m",
                 "options": {"temperature": temperatura, "num_ctx": 8192, "num_predict": num_predict}}
        if mendon:
            trupi["think"] = True
        if format_json:
            trupi["format"] = "json"
        pergjigja, mendimi = [], []
        try:
            koha = (KOHA_KRYESORI, 900) if i < len(radha) - 1 else 900   # (lidhja + copa e parë, gjithsej)
            with requests.post(f"{OLLAMA_URL}/api/chat", json=trupi, stream=True, timeout=koha) as r:
                r.raise_for_status()
                for rresht in r.iter_lines():
                    if not rresht:
                        continue
                    m = _json.loads(rresht).get("message") or {}
                    if copa := m.get("thinking"):
                        mendimi.append(copa)
                        if on_mendim:
                            on_mendim(copa)
                    if copa := m.get("content"):
                        pergjigja.append(copa)
                        if on_pergjigje:
                            on_pergjigje(copa)
            if not "".join(pergjigja).strip():
                raise ValueError("përgjigje bosh")
            MODELI_I_FUNDIT.update(modeli=model, rezerve=i > 0)
            if i > 0:
                log.warning("Mendimi: u përdor %s (modeli i parë dështoi: %s)", model, gabimi)
            return "".join(pergjigja).strip(), "".join(mendimi).strip()
        except (requests.RequestException, ValueError) as e:
            gabimi = e
            log.warning("Modeli %s dështoi: %s", model, e)
            if pergjigja and on_pergjigje:
                raise   # përgjigja ka filluar t'i shfaqet personit: nuk e nisim nga e para me model tjetër
    raise gabimi


def normalizo(tekst: str) -> str:
    """Shkronja të vogla dhe pa ë/ç, që 'me dhemb' dhe 'më dhemb' të jenë njësoj."""
    tekst = unicodedata.normalize("NFKD", tekst.lower())
    tekst = "".join(c for c in tekst if not unicodedata.combining(c))
    return " ".join(tekst.split())
