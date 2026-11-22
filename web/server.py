"""FarmaBot Web: serveri (Starlette) për ndërfaqen në stilin e ChatGPT / Claude.

    python -m web            → http://localhost:8501

API (JSON):
  GET  /api/sesioni                     kush je, profili, gjendjet
  POST /api/hyr | /api/regjistrohu | /api/vizitor | /api/dil
  GET  /api/bisedat                     lista e bisedave
  GET  /api/bisedat/{id}                mesazhet e një bisede
  PATCH/DELETE /api/bisedat/{id}        riemërto / fshi
  POST /api/biseda                      mesazh i ri → NDJSON live: hapat, mendimi, përgjigjja
  PUT  /api/profili                     mosha, gjendjet, alergjitë
  POST /api/fjalekalimi, DELETE /api/llogaria
  /api/admin/...                        shiko web/admin.py

Vizitorët (pa llogari): profili dhe bisedat mbahen vetëm në kujtesën e serverit, për sesionin.
Siguria e përgjigjeve nuk ndryshon: urgjencat, filtrimi i barnave dhe dozat vijnë nga chatbot.py dhe Neo4j.
"""
import asyncio
import contextlib
import json
import os
import secrets
import threading
import time
import uuid
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, StreamingResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

import bisedat as db_b
import llogarite
import perdoruesit as db_p
from chatbot import Konteksti, Profili, pergjigju
from config import ROOT, query
from web import admin
from web.pergjigja import pa_emoji, te_dhenat

STATIKE = Path(__file__).parent / "static"
AUTOMATIKE = {"femije_nen_12", "nen_16", "mbi_65"}  # llogariten nga mosha, nuk zgjidhen me dorë


# ---------------------------------------------------------------- ndihmëse
def _sekreti() -> str:
    """Çelësi që nënshkruan cookie-n e sesionit. Krijohet një herë dhe ruhet te .env."""
    if s := os.getenv("SESSION_SECRET"):
        return s
    s = secrets.token_urlsafe(32)
    env = ROOT / ".env"
    tekst = env.read_text(encoding="utf-8") if env.exists() else ""
    env.write_text(tekst.rstrip("\n") + f"\nSESSION_SECRET={s}\n", encoding="utf-8")
    os.environ["SESSION_SECRET"] = s
    return s


def gabim(mesazh: str, kodi: int = 400) -> JSONResponse:
    return JSONResponse({"gabim": mesazh}, status_code=kodi)


async def trupi(request: Request) -> dict:
    try:
        d = await request.json()
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


def llogaria(request: Request) -> dict | None:
    return request.session.get("llogaria")


VIZITORET: dict[str, dict] = {}  # id → {"profili": {...}, "bisedat": {bid: {...}}, "ora": time}
_bllok = threading.Lock()


def _vizitori(request: Request) -> dict | None:
    vid = request.session.get("vizitor")
    if not vid:
        return None
    with _bllok:
        if len(VIZITORET) > 500:  # pastro sesionet më të vjetra
            for k in sorted(VIZITORET, key=lambda k: VIZITORET[k]["ora"])[:100]:
                VIZITORET.pop(k, None)
        v = VIZITORET.setdefault(vid, {"profili": {"mosha": None, "gjendjet": [], "shenime": ""},
                                       "bisedat": {}, "ora": time.time()})
        v["ora"] = time.time()
        return v


def _profili(request: Request) -> dict:
    if (l := llogaria(request)) and l.get("person_id"):
        p = db_p.merr_person(l["person_id"]) or {}
        return {"emer": p.get("emer"), "mosha": p.get("mosha"), "gjendjet": p.get("gjendjet") or [],
                "shenime": p.get("shenime") or ""}
    v = _vizitori(request)
    return dict(v["profili"]) if v else {"mosha": None, "gjendjet": [], "shenime": ""}


def _gjendjet() -> list[dict]:
    return query("MATCH (g:Gjendje) RETURN g.id AS id, g.emer AS emer ORDER BY g.emer")


def _titulli(mesazh: str) -> str:
    t = " ".join(pa_emoji(mesazh).split())
    return (t[:48].rsplit(" ", 1)[0] + "…") if len(t) > 50 else (t or "Bisedë e re")


# ---------------------------------------------------------------- faqja dhe sesioni
async def faqja(request: Request):
    return FileResponse(STATIKE / "index.html", headers={"Cache-Control": "no-cache"})


async def sesioni(request: Request):
    l = llogaria(request)
    return JSONResponse({
        "llogaria": {"perdoruesi": l["perdoruesi"], "roli": l["roli"]} if l else None,
        "vizitor": bool(request.session.get("vizitor")) and not l,
        "profili": _profili(request) if (l or request.session.get("vizitor")) else None,
        "gjendjet": [g for g in _gjendjet() if g["id"] not in AUTOMATIKE],
    })


async def hyr(request: Request):
    d = await trupi(request)
    u, fj = str(d.get("perdoruesi") or "").strip(), str(d.get("fjalekalimi") or "")
    l = llogarite.hyr(u, fj)
    if not l and fj != fj.strip():  # hapësira të kopjuara bashkë me fjalëkalimin
        l = llogarite.hyr(u, fj.strip())
    if not l:
        return gabim("Emri ose fjalëkalimi nuk është i saktë.", 401)
    request.session.clear()
    request.session["llogaria"] = l
    return await sesioni(request)


async def regjistrohu(request: Request):
    d = await trupi(request)
    u, fj, emer = d.get("perdoruesi", ""), d.get("fjalekalimi", ""), (d.get("emer") or "").strip()
    if e := llogarite.valido(u, fj) or llogarite.valido_emrin(emer):
        return gabim(e)
    if not d.get("pelqim"):
        return gabim("Duhet pëlqimi për të ruajtur të dhënat.")
    mosha = d.get("mosha")
    try:
        mosha = int(mosha) if mosha not in (None, "") else None
        llogarite.krijo_llogari(u, fj, "perdorues", emer or None, mosha)
    except ValueError as e:
        return gabim(str(e))
    request.session.clear()
    request.session["llogaria"] = llogarite.hyr(u, fj)
    return await sesioni(request)


async def vizitor(request: Request):
    request.session.clear()
    request.session["vizitor"] = uuid.uuid4().hex
    _vizitori(request)
    return await sesioni(request)


async def dil(request: Request):
    VIZITORET.pop(request.session.get("vizitor") or "", None)
    request.session.clear()
    return JSONResponse({"ok": True})


def _kerkon_sesion(f):
    async def w(request: Request):
        if not llogaria(request) and not request.session.get("vizitor"):
            return gabim("Sesioni ka mbaruar. Hyr përsëri.", 401)
        return await f(request)
    return w


# ---------------------------------------------------------------- profili dhe llogaria
@_kerkon_sesion
async def profili_ruaj(request: Request):
    d = await trupi(request)
    lejuara = {g["id"] for g in _gjendjet()} - AUTOMATIKE
    gjendjet = {g for g in d.get("gjendjet") or [] if g in lejuara}
    try:
        mosha = int(d["mosha"]) if d.get("mosha") not in (None, "") else None
    except (TypeError, ValueError):
        return gabim("Mosha nuk është e vlefshme.")
    if mosha is not None and not 0 <= mosha <= 110:
        return gabim("Mosha duhet të jetë 0–110.")
    shenime = str(d.get("shenime") or "")[:500]
    if (l := llogaria(request)) and l.get("person_id"):
        db_p.perditeso_person(l["person_id"], mosha=mosha, gjendjet=gjendjet, shenime=shenime)
    elif v := _vizitori(request):
        v["profili"] = {"mosha": mosha, "gjendjet": sorted(gjendjet), "shenime": shenime}
    return JSONResponse({"profili": _profili(request)})


async def fjalekalimi(request: Request):
    l = llogaria(request)
    if not l:
        return gabim("Hyr në llogari.", 401)
    d = await trupi(request)
    if not llogarite.hyr(l["perdoruesi"], d.get("aktual", "")):
        return gabim("Fjalëkalimi aktual nuk është i saktë.")
    try:
        llogarite.ndrysho_fjalekalimin(l["perdoruesi"], d.get("i_ri", ""))
    except ValueError as e:
        return gabim(str(e))
    return JSONResponse({"ok": True})


async def fshi_llogarine(request: Request):
    l = llogaria(request)
    if not l:
        return gabim("Hyr në llogari.", 401)
    try:
        llogarite.fshi_llogari(l["perdoruesi"])
    except ValueError as e:
        return gabim(str(e))
    request.session.clear()
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------- bisedat
@_kerkon_sesion
async def bisedat_lista(request: Request):
    if (l := llogaria(request)) and l.get("person_id"):
        return JSONResponse({"bisedat": db_b.lista(l["person_id"])})
    v = _vizitori(request)
    lista = [{"id": bid, "titull": b["titull"], "perditesuar": b["perditesuar"]} for bid, b in v["bisedat"].items()]
    return JSONResponse({"bisedat": sorted(lista, key=lambda b: b["perditesuar"], reverse=True)})


def _biseda_e_vizitorit(request: Request, bid: str) -> dict | None:
    v = _vizitori(request)
    return v["bisedat"].get(bid) if v else None


@_kerkon_sesion
async def biseda_merr(request: Request):
    bid = request.path_params["bid"]
    if (l := llogaria(request)) and l.get("person_id"):
        if not db_b.i_perket(l["person_id"], bid):
            return gabim("Biseda nuk u gjet.", 404)
        return JSONResponse({"mesazhet": db_b.mesazhet(bid)})
    b = _biseda_e_vizitorit(request, bid)
    return JSONResponse({"mesazhet": b["mesazhet"]}) if b else gabim("Biseda nuk u gjet.", 404)


@_kerkon_sesion
async def biseda_ndrysho(request: Request):
    bid = request.path_params["bid"]
    titull = " ".join(str((await trupi(request)).get("titull") or "").split())[:80]
    if not titull:
        return gabim("Titulli është bosh.")
    if (l := llogaria(request)) and l.get("person_id"):
        if not db_b.i_perket(l["person_id"], bid):
            return gabim("Biseda nuk u gjet.", 404)
        db_b.riemerto(bid, titull)
    elif b := _biseda_e_vizitorit(request, bid):
        b["titull"] = titull
    return JSONResponse({"ok": True})


@_kerkon_sesion
async def biseda_fshi(request: Request):
    bid = request.path_params["bid"]
    if (l := llogaria(request)) and l.get("person_id"):
        if not db_b.i_perket(l["person_id"], bid):
            return gabim("Biseda nuk u gjet.", 404)
        db_b.fshi(bid)
    elif v := _vizitori(request):
        v["bisedat"].pop(bid, None)
    return JSONResponse({"ok": True})


@_kerkon_sesion
async def biseda_mesazh(request: Request):
    """Mesazh i ri. Përgjigjja vjen live si NDJSON: {"lloji": "bisede"|"hap"|"mendim"|"fund"|"gabim", ...}."""
    d = await trupi(request)
    mesazh = str(d.get("mesazh") or "").strip()[:2000]
    if not mesazh:
        return gabim("Mesazhi është bosh.")
    mendo = bool(d.get("mendo"))
    gjuha = d.get("gjuha") if d.get("gjuha") in ("sq", "en") else None  # gjuha e zgjedhur në ndërfaqe
    l = llogaria(request)
    pid = l.get("person_id") if l else None
    bid = d.get("bisede_id")

    # biseda: e re ose ekzistuese
    if pid:
        if bid and not db_b.i_perket(pid, bid):
            return gabim("Biseda nuk u gjet.", 404)
        if not bid:
            bid = db_b.krijo(pid, _titulli(mesazh))
        historia = [{"role": m["role"], "content": m["content"]} for m in db_b.mesazhet(bid)]
        k = db_b.konteksti(bid)
    else:
        v = _vizitori(request)
        if bid and bid not in v["bisedat"]:
            return gabim("Biseda nuk u gjet.", 404)
        if not bid:
            bid = uuid.uuid4().hex
            v["bisedat"][bid] = {"titull": _titulli(mesazh), "perditesuar": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 "mesazhet": [], "konteksti": {}}
        historia = [{"role": m["role"], "content": m["content"]} for m in v["bisedat"][bid]["mesazhet"]]
        k = v["bisedat"][bid]["konteksti"]

    prof = _profili(request)
    mosha = k.get("mosha_bisedes", prof.get("mosha"))
    profili = Profili(mosha=mosha, gjendjet=set(prof.get("gjendjet") or []), shenime=(prof.get("shenime") or "").strip())
    konteksti = Konteksti(simptomat=k.get("simptomat", []), barnat=k.get("barnat", []),
                          pritje=k.get("pritje", []), pritje_shto=k.get("pritje_shto", False))

    loop = asyncio.get_running_loop()
    radha: asyncio.Queue = asyncio.Queue()

    def dergo(obj):
        loop.call_soon_threadsafe(radha.put_nowait, obj)

    def puno():
        try:
            p = pergjigju(mesazh, historia, profili, konteksti=konteksti, mendo=mendo, gjuha=gjuha,
                          on_hap=lambda h: dergo({"lloji": "hap", "tekst": pa_emoji(h)}),
                          on_mendim=lambda c: dergo({"lloji": "mendim", "tekst": c}))
            td = te_dhenat(p)
            # konteksti i bisedës për mesazhin e ardhshëm
            if p.simptomat:
                k["simptomat"] = [s["id"] for s in p.simptomat]
            if p.barnat_konteksti:
                k["barnat"] = p.barnat_konteksti
            if not p.urgjence:
                k["pritje"], k["pritje_shto"] = p.pritje, p.pritje_shto
            if p.mosha_e_re is not None:
                k["mosha_bisedes"] = p.mosha_e_re   # p.sh. "djali 5 vjeç": vlen vetëm për këtë bisedë
            simptomat = [s["id"] for s in p.simptomat]
            barnat = [b["id"] for b in p.barnat] or p.barnat_konteksti
            if pid:
                db_b.ruaj_mesazh(pid, bid, "user", mesazh)
                db_b.ruaj_mesazh(pid, bid, "assistant", td["tekst"], simptomat, barnat, td)
                db_b.ruaj_kontekstin(bid, k)
                db_p.shto_gjendje(pid, p.gjendje_te_reja)
                if p.mosha_e_re is not None and prof.get("mosha") is None:
                    db_p.perditeso_person(pid, mosha=p.mosha_e_re)
            else:
                b = v["bisedat"][bid]
                b["mesazhet"] += [{"role": "user", "content": mesazh, "te_dhena": None},
                                  {"role": "assistant", "content": td["tekst"], "te_dhena": td}]
                b["perditesuar"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                v["profili"]["gjendjet"] = sorted(set(v["profili"]["gjendjet"]) | p.gjendje_te_reja)
                if p.mosha_e_re is not None and v["profili"]["mosha"] is None:
                    v["profili"]["mosha"] = p.mosha_e_re
            dergo({"lloji": "fund", "pergjigja": td, "profili": _profili(request) if (p.gjendje_te_reja or p.mosha_e_re is not None) else None})
        except Exception as e:  # noqa: BLE001 — gabimi i tregohet personit, jo serverit që bie
            dergo({"lloji": "gabim", "tekst": f"{e}"})
        finally:
            dergo(None)

    async def rrjedha():
        yield json.dumps({"lloji": "bisede", "id": bid, "titull": _titulli(mesazh) if not d.get("bisede_id") else None},
                         ensure_ascii=False) + "\n"
        threading.Thread(target=puno, daemon=True).start()
        while (obj := await radha.get()) is not None:
            yield json.dumps(obj, ensure_ascii=False) + "\n"

    return StreamingResponse(rrjedha(), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------------------------------------------------------------- aplikacioni
def krijo_aplikacionin() -> Starlette:
    rruget = [
        Route("/", faqja),
        Route("/api/sesioni", sesioni),
        Route("/api/hyr", hyr, methods=["POST"]),
        Route("/api/regjistrohu", regjistrohu, methods=["POST"]),
        Route("/api/vizitor", vizitor, methods=["POST"]),
        Route("/api/dil", dil, methods=["POST"]),
        Route("/api/profili", profili_ruaj, methods=["PUT"]),
        Route("/api/fjalekalimi", fjalekalimi, methods=["POST"]),
        Route("/api/llogaria", fshi_llogarine, methods=["DELETE"]),
        Route("/api/bisedat", bisedat_lista),
        Route("/api/bisedat/{bid}", biseda_merr, methods=["GET"]),
        Route("/api/bisedat/{bid}", biseda_ndrysho, methods=["PATCH"]),
        Route("/api/bisedat/{bid}", biseda_fshi, methods=["DELETE"]),
        Route("/api/biseda", biseda_mesazh, methods=["POST"]),
        *admin.rruget(llogaria, trupi, gabim),
        Mount("/static", StaticFiles(directory=STATIKE), name="static"),
        Mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets"),
    ]
    mw = [Middleware(SessionMiddleware, secret_key=_sekreti(), session_cookie="farmabot",
                      max_age=60 * 60 * 24 * 14, same_site="lax", https_only=False)]

    @contextlib.asynccontextmanager
    async def jeta(_app):
        db_p.krijo_skemen()
        db_b.krijo_skemen()
        llogarite.sigurohu_per_admin()
        yield

    return Starlette(routes=rruget, middleware=mw, lifespan=jeta)


app = krijo_aplikacionin()
