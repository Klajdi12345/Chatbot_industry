"""Claude AI (Anthropic) si motor gjuhësor i FarmaBot-it.

Çfarë sjell Claude:
  * mendim i thellë (adaptive thinking) me arsyetim të përmbledhur që shfaqet live te ndërfaqja;
  * nivel përpjekjeje (effort): low / medium / high, i zgjedhshëm nga paneli;
  * shikim (vision): lexon foton e kutisë së ilaçit ose të fletëudhëzuesit;
  * prompt caching për promptet e sistemit (më lirë dhe më shpejt në bisedat e gjata);
  * fallback nga serveri nëse modeli refuzon një kërkesë.

Siguria nuk ndryshon: urgjencat, filtrimi i barnave dhe dozat vijnë gjithmonë nga rregullat dhe databaza.
Embeddings (bge-m3) mbeten lokale te Ollama.

Konfigurimi te .env:
  ANTHROPIC_API_KEY=sk-ant-...      (ose `ant auth login`)
  LLM_PROVIDER=auto | claude | ollama   (auto = Claude nëse ka çelës, përndryshe Ollama)
  CLAUDE_MODEL=claude-opus-5-5
  CLAUDE_EFFORT=medium
"""
from __future__ import annotations

import base64
import json
import os
import re
from functools import lru_cache

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
EFFORT = os.getenv("CLAUDE_EFFORT", "medium")
NIVELET = ("low", "medium", "high")
_BETAS = ["server-side-fallback-2026-07-01"]


class RefuzimClaude(RuntimeError):
    """Claude e refuzoi kërkesën (stop_reason == 'refusal')."""


@lru_cache
def _klienti():
    import anthropic
    return anthropic.Anthropic(timeout=300.0, max_retries=2)


def ka_kredenciale() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


def _ndaj_sistemin(mesazhet: list[dict]) -> tuple[list[dict], list[dict]]:
    """Formati i Ollama-s (role=system brenda listës) → system + messages për Claude."""
    sistemi, tjera = [], []
    for m in mesazhet:
        if m["role"] == "system":
            sistemi.append(m["content"])
        elif m.get("content"):
            tjera.append({"role": m["role"], "content": m["content"]})
    while tjera and tjera[0]["role"] != "user":  # mesazhi i parë duhet të jetë i përdoruesit
        tjera.pop(0)
    blloqet = [{"type": "text", "text": "\n\n".join(sistemi), "cache_control": {"type": "ephemeral"}}] if sistemi else []
    return blloqet, tjera or [{"role": "user", "content": "..."}]


def _efforti(effort: str | None) -> str:
    e = (effort or os.getenv("CLAUDE_EFFORT") or EFFORT).lower()
    return e if e in NIVELET else "medium"


def _kontrollo(mesazhi):
    if mesazhi.stop_reason == "refusal":
        raise RefuzimClaude("Claude nuk e përpunoi këtë kërkesë.")


def _tekst(mesazhi) -> str:
    return "".join(b.text for b in mesazhi.content if b.type == "text").strip()


def chat(mesazhet: list[dict], effort: str | None = "low", max_tokens: int = 4000) -> str:
    """Përgjigje e thjeshtë (pa shfaqur arsyetimin)."""
    sistemi, mesazhet = _ndaj_sistemin(mesazhet)
    with _klienti().beta.messages.stream(
        model=MODEL, max_tokens=max_tokens, system=sistemi, messages=mesazhet,
        output_config={"effort": _efforti(effort)},
        betas=_BETAS, fallbacks="default",
    ) as s:
        m = s.get_final_message()
    _kontrollo(m)
    return _tekst(m)


def chat_mendo(mesazhet: list[dict], on_mendim=None, on_pergjigje=None, format_json: bool = False,
               effort: str | None = None, max_tokens: int = 16000) -> tuple[str, str]:
    """Me mendim të thellë dhe streaming. Kthen (pergjigja, mendimi)."""
    sistemi, mesazhet = _ndaj_sistemin(mesazhet)
    if format_json:
        sistemi.append({"type": "text", "text": "Përgjigju vetëm me një objekt JSON të vlefshëm, pa tekst tjetër."})
    pergjigja, mendimi = [], []
    with _klienti().beta.messages.stream(
        model=MODEL, max_tokens=max_tokens, system=sistemi, messages=mesazhet,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": _efforti(effort)},
        betas=_BETAS, fallbacks="default",
    ) as s:
        for ngjarje in s:
            if ngjarje.type != "content_block_delta":
                continue
            d = ngjarje.delta
            if d.type == "thinking_delta" and d.thinking:
                mendimi.append(d.thinking)
                if on_mendim:
                    on_mendim(d.thinking)
            elif d.type == "text_delta" and d.text:
                pergjigja.append(d.text)
                if on_pergjigje:
                    on_pergjigje(d.text)
        m = s.get_final_message()
    _kontrollo(m)
    return "".join(pergjigja).strip(), "".join(mendimi).strip()


# ---------------------------------------------------------------- shikimi (foto e ilaçit)
PROMPT_FOTO = """Ti je pjesa "shikimi" e FarmaBot-it, një asistenti farmacie në shqip.
Personi ka dërguar një foto: zakonisht kutinë e një ilaçi, një fletëudhëzues ose një blister.
Lexo vetëm atë që shihet qartë në foto. Mos hamendëso emra që nuk lexohen.

Kthe VETËM JSON:
{"eshte_ilac": true/false,
 "emrat_tregtare": ["emrat e shkruar në kuti, p.sh. Panadol"],
 "lende_aktive": ["lëndët aktive në shqip ose me emrin ndërkombëtar, p.sh. paracetamol"],
 "forca": "p.sh. 500 mg, ose bosh",
 "pershkrim": "1–2 fjali në shqip: çfarë shihet në foto"}"""

LLOJET_FOTO = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp", "gif": "image/gif"}


def lexo_foton(te_dhenat: bytes, lloji: str, shenim: str = "") -> dict:
    """Claude Vision lexon foton e ilaçit. Kthen emrat dhe lëndët aktive që shihen në foto."""
    mesazh = [{"type": "image", "source": {"type": "base64", "media_type": lloji,
                                           "data": base64.standard_b64encode(te_dhenat).decode()}},
              {"type": "text", "text": f"Shënimi i personit: {shenim}" if shenim else "Çfarë ilaçi është ky?"}]
    with _klienti().beta.messages.stream(
        model=MODEL, max_tokens=4000,
        system=[{"type": "text", "text": PROMPT_FOTO, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": mesazh}],
        output_config={"effort": "low"}, betas=_BETAS, fallbacks="default",
    ) as s:
        m = s.get_final_message()
    _kontrollo(m)
    gjetja = re.search(r"\{.*\}", _tekst(m), re.S)
    try:
        d = json.loads(gjetja.group(0)) if gjetja else {}
    except ValueError:
        d = {}

    def lista(k):
        return [str(x).strip() for x in d.get(k) or [] if str(x).strip()]

    return {"eshte_ilac": bool(d.get("eshte_ilac")), "emrat_tregtare": lista("emrat_tregtare"),
            "lende_aktive": lista("lende_aktive"), "forca": str(d.get("forca") or "").strip(),
            "pershkrim": str(d.get("pershkrim") or "").strip()}
