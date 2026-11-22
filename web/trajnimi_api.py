"""API e trajnimit: reagimet 👍/👎 nga përdoruesit dhe paneli "Trajnimi" i administratorit.

  POST /api/reagim                             çdo sesion (edhe vizitori): vlerëso një përgjigje
  GET  /api/admin/trajnimi                     vlerësimi i fundit, historiku, reagimet e hapura, mësimet
  POST /api/admin/trajnimi/vlereso             nis vlerësimin në sfond (progresi lexohet me GET)
  POST /api/admin/trajnimi/meso                mësoji botit një frazë → simptomë (opsionale: mbyll reagimin)
  POST /api/admin/trajnimi/reagim/{id}/zgjidh  shëno reagimin si të zgjidhur
"""
import json
import threading

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from trajnimi import meso, reagimet, vlereso

_PUNA = {"aktive": False, "i": 0, "n": 0, "kategoria": "", "gabim": None}
_bllok = threading.Lock()


def _nis_vleresimin():
    def puno():
        try:
            r = vlereso.vlereso(on_progres=lambda i, n, k: _PUNA.update(i=i, n=n, kategoria=k))
            vlereso.ruaj(r)
            _PUNA["gabim"] = None
        except Exception as e:  # noqa: BLE001
            _PUNA["gabim"] = str(e)
        finally:
            _PUNA["aktive"] = False

    with _bllok:
        if _PUNA["aktive"]:
            return False
        _PUNA.update(aktive=True, i=0, n=0, kategoria="", gabim=None)
    threading.Thread(target=puno, daemon=True).start()
    return True


def rruget(llogaria, trupi, gabim, ka_sesion) -> list[Route]:
    def vetem_admin(f):
        async def w(request: Request):
            l = llogaria(request)
            if not l or l.get("roli") != "admin":
                return gabim("Vetëm për administratorin.", 403)
            return await f(request, l)
        return w

    async def reagim(request: Request):
        if not ka_sesion(request):
            return gabim("Sesioni ka mbaruar. Hyr përsëri.", 401)
        d = await trupi(request)
        try:
            l = llogaria(request)
            rid = await run_in_threadpool(
                reagimet.ruaj, int(d.get("vlera") or 0), str(d.get("pyetja") or ""), str(d.get("pergjigjja") or ""),
                str(d.get("arsye") or ""), str(d.get("koment") or ""),
                [str(x) for x in (d.get("simptomat") or [])][:10], "en" if d.get("gjuha") == "en" else "sq",
                l["perdoruesi"] if l else None)
        except (TypeError, ValueError) as e:
            return gabim(str(e))
        return JSONResponse({"id": rid})

    @vetem_admin
    async def permbledhje(request, l):
        i_fundit = vlereso.i_fundit()
        if i_fundit:
            i_fundit = {k: v for k, v in i_fundit.items() if k != "rezultatet"}
        mesimet = json.loads(meso.REGJISTRI.read_text(encoding="utf-8")) if meso.REGJISTRI.exists() else []
        return JSONResponse({
            "i_fundit": i_fundit, "historiku": vlereso.historiku()[-12:], "puna": dict(_PUNA),
            "reagimet": reagimet.lista(), "numrat": reagimet.numrat(),
            "simptomat": meso.lista_simptomave(), "mesimet": list(reversed(mesimet))[:15],
        })

    @vetem_admin
    async def nis(request, l):
        if not _nis_vleresimin():
            return gabim("Një vlerësim po punon tashmë.", 409)
        return JSONResponse({"ok": True})

    @vetem_admin
    async def meso_fraze(request, l):
        d = await trupi(request)
        try:
            r = await run_in_threadpool(meso.meso_fraze, str(d.get("fraza") or ""), str(d.get("simptoma") or ""),
                                        l["perdoruesi"], "reagim" if d.get("reagim_id") else "manual")
        except ValueError as e:
            return gabim(str(e))
        if d.get("reagim_id"):
            reagimet.zgjidh(str(d["reagim_id"]), f"U mësua si: {r['simptoma']}")
        return JSONResponse(r)

    @vetem_admin
    async def zgjidh(request, l):
        d = await trupi(request)
        if not reagimet.zgjidh(request.path_params["rid"], str(d.get("zgjidhja") or "U shqyrtua")):
            return gabim("Reagimi nuk u gjet.", 404)
        return JSONResponse({"ok": True})

    return [
        Route("/api/reagim", reagim, methods=["POST"]),
        Route("/api/admin/trajnimi", permbledhje),
        Route("/api/admin/trajnimi/vlereso", nis, methods=["POST"]),
        Route("/api/admin/trajnimi/meso", meso_fraze, methods=["POST"]),
        Route("/api/admin/trajnimi/reagim/{rid}/zgjidh", zgjidh, methods=["POST"]),
    ]
