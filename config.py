"""Konfigurimi i përbashkët: lidhja me Neo4j dhe modelet e Ollama-s."""
import contextvars
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


# ---------------------------------------------------------------- motori gjuhësor: Claude ose Ollama
# LLM_PROVIDER=auto (parazgjedhja): Claude nëse ka ANTHROPIC_API_KEY, përndryshe Ollama lokal.
# Paneli i bisedës mund ta ndryshojë për sesionin (vendos_motorin).

_motori_sesionit: contextvars.ContextVar[str | None] = contextvars.ContextVar("motori", default=None)
_efforti_sesionit: contextvars.ContextVar[str | None] = contextvars.ContextVar("efforti", default=None)


def motori_parazgjedhur() -> str:
    import claude_ai
    p = os.getenv("LLM_PROVIDER", "auto").lower()
    if p in ("claude", "ollama"):
        return p
    return "claude" if claude_ai.ka_kredenciale() else "ollama"


def vendos_motorin(motori: str | None, effort: str | None = None):
    """Për kërkesën aktuale: 'claude' ose 'ollama' (None = parazgjedhja nga .env)."""
    _motori_sesionit.set(motori)
    _efforti_sesionit.set(effort)


def motori() -> str:
    return _motori_sesionit.get() or motori_parazgjedhur()


def emri_motorit() -> str:
    import claude_ai
    return f"Claude · {claude_ai.MODEL}" if motori() == "claude" else f"Ollama · {LLM_MODEL}"


def chat(mesazhet: list[dict]) -> str:
    """mesazhet: [{'role': 'system'|'user'|'assistant', 'content': ...}]"""
    if motori() == "claude":
        import claude_ai
        return claude_ai.chat(mesazhet, effort="low")
    r = requests.post(f"{OLLAMA_URL}/api/chat", json={
        "model": LLM_MODEL, "messages": mesazhet, "stream": False,
        "options": {"temperature": 0.5, "num_ctx": 4096}, "keep_alive": "30m",
    }, timeout=600)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


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
    if motori() == "claude":
        import claude_ai
        return claude_ai.chat_mendo(mesazhet, on_mendim=on_mendim, on_pergjigje=on_pergjigje,
                                    format_json=format_json,
                                    effort="low" if format_json else _efforti_sesionit.get())
    import json as _json
    model, mendon = modeli_i_mendimit()
    trupi = {"model": model, "messages": mesazhet, "stream": True, "keep_alive": "30m",
             "options": {"temperature": temperatura, "num_ctx": 8192, "num_predict": num_predict}}
    if mendon:
        trupi["think"] = True
    if format_json:
        trupi["format"] = "json"
    pergjigja, mendimi = [], []
    with requests.post(f"{OLLAMA_URL}/api/chat", json=trupi, stream=True, timeout=900) as r:
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
    return "".join(pergjigja).strip(), "".join(mendimi).strip()


def normalizo(tekst: str) -> str:
    """Shkronja të vogla dhe pa ë/ç, që 'me dhemb' dhe 'më dhemb' të jenë njësoj."""
    tekst = unicodedata.normalize("NFKD", tekst.lower())
    tekst = "".join(c for c in tekst if not unicodedata.combining(c))
    return " ".join(tekst.split())
