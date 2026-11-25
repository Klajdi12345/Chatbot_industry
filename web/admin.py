"""API e administratorit: përmbledhja, përdoruesit, ilaçet dhe backup-i. Vetëm për rolin 'admin'."""
import json

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

import backup
import bisedat as db_b
import chatbot
import llogarite
import perdoruesit as db_p
from config import ROOT, menyra_lidhjes, query

SKEDARI_NJOHURIVE = ROOT / "data" / "njohurite.json"
FUSHAT_E_NDRYSHUESHME = ["emer", "doza", "doza_maks", "kohezgjatja", "si_merret"]


def _ruaj_ne_json(perditesime: dict[str, dict] | None = None, i_ri: dict | None = None):
    """Ndryshimet ruhen edhe te njohurite.json, që `ngarko_grafin.py` të mos i fshijë."""
    data = json.loads(SKEDARI_NJOHURIVE.read_text(encoding="utf-8"))
    for b in data["barnat"]:
        b.update((perditesime or {}).get(b["id"], {}))
    if i_ri:
        data["barnat"].append(i_ri["barna"])
        for s in data["simptomat"]:
            if s["id"] in i_ri["simptomat"] and i_ri["barna"]["id"] not in s["barnat"]:
                s["barnat"].append(i_ri["barna"]["id"])
    SKEDARI_NJOHURIVE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def rruget(llogaria, trupi, gabim) -> list[Route]:
    def vetem_admin(f):
        async def w(request: Request):
            l = llogaria(request)
            if not l or l.get("roli") != "admin":
                return gabim("Vetëm për administratorin.", 403)
            return await f(request, l)
        return w

    @vetem_admin
    async def permbledhje(request, l):
        n = query("""
            CALL () { MATCH (l:Llogari) RETURN count(l) AS llogari }
            CALL () { MATCH (p:Person) RETURN count(p) AS persona }
            CALL () { MATCH (m:Mesazh {roli: 'user'}) RETURN count(m) AS pyetje }
            CALL () { MATCH (b:Barna) RETURN count(b) AS barna }
            CALL () { MATCH (s:Simptome) RETURN count(s) AS simptoma }
            RETURN llogari, persona, pyetje, barna, simptoma""")[0]
        return JSONResponse({
            "numrat": n, "lidhja": menyra_lidhjes().upper(),
            "simptomat": query("MATCH (:Mesazh)-[:PER_SIMPTOMEN]->(s:Simptome) "
                               "RETURN s.emer AS emer, count(*) AS here ORDER BY here DESC LIMIT 8"),
            "barnat": query("MATCH (:Mesazh)-[:SUGJEROI]->(b:Barna) "
                            "RETURN b.emer AS emer, count(*) AS here ORDER BY here DESC LIMIT 8"),
            "pyetjet": query("MATCH (p:Person)-[:DERGOI]->(m:Mesazh {roli: 'user'}) "
                             "RETURN substring(toString(m.ora), 0, 16) AS ora, p.emer AS personi, m.tekst AS tekst "
                             "ORDER BY m.ora DESC LIMIT 12"),
        })

    @vetem_admin
    async def perdoruesit(request, l):
        lista = llogarite.lista_llogarive()
        return JSONResponse({"une": l["perdoruesi"], "llogarite": [
            {**x, "krijuar": (x["krijuar"] or "")[:16].replace("T", " "),
             "hyrja_fundit": (x["hyrja_fundit"] or "")[:16].replace("T", " ")} for x in lista]})

    @vetem_admin
    async def perdorues_krijo(request, l):
        d = await trupi(request)
        try:
            llogarite.krijo_llogari(d.get("perdoruesi", ""), d.get("fjalekalimi", ""),
                                    d.get("roli") if d.get("roli") in llogarite.ROLET else "perdorues",
                                    (d.get("emer") or "").strip() or None, email=str(d.get("email") or "").strip() or None)
        except ValueError as e:
            return gabim(str(e))
        return JSONResponse({"ok": True})

    @vetem_admin
    async def perdorues_ndrysho(request, l):
        u, d = request.path_params["u"], await trupi(request)
        try:
            if d.get("roli"):
                llogarite.ndrysho_rolin(u, d["roli"])
            if d.get("fjalekalimi"):
                llogarite.ndrysho_fjalekalimin(u, d["fjalekalimi"])
        except ValueError as e:
            return gabim(str(e))
        return JSONResponse({"ok": True})

    @vetem_admin
    async def perdorues_fshi(request, l):
        u = request.path_params["u"]
        if llogarite.normalizo_perdoruesin(u) == l["perdoruesi"]:
            return gabim("Nuk mund ta fshish llogarinë me të cilën je i futur.")
        try:
            llogarite.fshi_llogari(u)
        except ValueError as e:
            return gabim(str(e))
        return JSONResponse({"ok": True})

    @vetem_admin
    async def perdorues_bisedat(request, l):
        u = llogarite.normalizo_perdoruesin(request.path_params["u"])
        rows = query("MATCH (:Llogari {perdoruesi: $u})-[:ESHTE]->(p:Person) RETURN p.id AS pid", u=u)
        if not rows or not rows[0]["pid"]:
            return JSONResponse({"profili": None, "bisedat": []})
        pid = rows[0]["pid"]
        bisedat = [{**b, "mesazhet": [{"role": m["role"], "content": m["content"], "ora": m["ora"][:16]}
                                      for m in db_b.mesazhet(b["id"])]} for b in db_b.lista_admin(pid)[:50]]
        return JSONResponse({"profili": db_p.merr_person(pid), "bisedat": bisedat})

    @vetem_admin
    async def barnat(request, l):
        rows = query("MATCH (b:Barna) OPTIONAL MATCH (s:Simptome)-[:TRAJTOHET_ME]->(b) "
                     "OPTIONAL MATCH (b)-[r:KUNDERINDIKOHET_PER|KUJDES_ME]->(g:Gjendje) "
                     "WITH b, collect(DISTINCT s.emer) AS simptomat, "
                     "collect(DISTINCT {lloji: type(r), gjendja: g.emer, arsye: r.arsye}) AS kufizime "
                     "RETURN b.id AS id, b.emer AS emer, b.doza AS doza, b.doza_maks AS doza_maks, "
                     "b.kohezgjatja AS kohezgjatja, b.si_merret AS si_merret, simptomat, "
                     "[k IN kufizime WHERE k.gjendja IS NOT NULL] AS kufizime ORDER BY b.emer")
        simptomat = query("MATCH (s:Simptome) RETURN s.id AS id, s.emer AS emer ORDER BY s.emer")
        gjendjet = query("MATCH (g:Gjendje) RETURN g.id AS id, g.emer AS emer ORDER BY g.emer")
        return JSONResponse({"barnat": rows, "simptomat": simptomat, "gjendjet": gjendjet})

    @vetem_admin
    async def barna_ndrysho(request, l):
        bid, d = request.path_params["bid"], await trupi(request)
        diff = {f: str(d[f]).strip() for f in FUSHAT_E_NDRYSHUESHME if f in d and str(d[f]).strip()}
        if not diff:
            return gabim("Asgjë për të ruajtur.")
        if not query("MATCH (b:Barna {id: $id}) SET b += $diff RETURN b.id AS id", id=bid, diff=diff):
            return gabim("Ilaçi nuk u gjet.", 404)
        _ruaj_ne_json({bid: diff})
        chatbot._te_gjitha_barnat.cache_clear()
        return JSONResponse({"ok": True})

    @vetem_admin
    async def barna_shto(request, l):
        d = await trupi(request)
        gjendjet = {r["id"]: r["emer"] for r in query("MATCH (g:Gjendje) RETURN g.id AS id, g.emer AS emer")}
        bid = str(d.get("id") or "").strip().lower().replace(" ", "_")
        emer, doza, per = str(d.get("emer") or "").strip(), str(d.get("doza") or "").strip(), d.get("per") or []
        if not (bid and emer and doza and per):
            return gabim("Plotëso të paktën ID-në, emrin, dozën dhe simptomat.")
        if query("MATCH (b:Barna {id: $id}) RETURN 1 AS x", id=bid):
            return gabim("Ky ID ekziston.")
        kunder = [g for g in d.get("kunder") or [] if g in gjendjet]
        kujdes = [g for g in d.get("kujdes") or [] if g in gjendjet]
        tregtare = [x.strip() for x in str(d.get("tregtare") or "").split(",") if x.strip()]
        barna = {"id": bid, "emer": emer, "lende_aktive": str(d.get("lende_aktive") or ""),
                 "forma": str(d.get("forma") or "Tableta"), "emra_tregtare": tregtare or [emer],
                 "doza": doza, "doza_maks": str(d.get("doza_maks") or ""),
                 "kohezgjatja": str(d.get("kohezgjatja") or ""), "si_merret": str(d.get("si_merret") or ""),
                 "paralajmerime": [], "efekte_anesore": [],
                 "kunderindikime": {g: f"Kundërindikohet: {gjendjet[g]}." for g in kunder},
                 "kujdes": {g: f"Kujdes: {gjendjet[g]}. Konsultohu me farmacistin." for g in kujdes}}
        props = {k: v for k, v in barna.items() if k not in ("kunderindikime", "kujdes")}
        query("CREATE (b:Barna) SET b = $props", props=props)
        for tipi, celesi in (("KUNDERINDIKOHET_PER", "kunderindikime"), ("KUJDES_ME", "kujdes")):
            query(f"MATCH (b:Barna {{id: $id}}) UNWIND $rows AS r MATCH (g:Gjendje {{id: r.g}}) "
                  f"MERGE (b)-[x:{tipi}]->(g) SET x.arsye = r.a", id=bid,
                  rows=[{"g": g, "a": a} for g, a in barna[celesi].items()])
        query("MATCH (b:Barna {id: $id}) UNWIND $per AS sid MATCH (s:Simptome {id: sid}) "
              "OPTIONAL MATCH (s)-[t:TRAJTOHET_ME]->() WITH b, s, count(t) AS n "
              "MERGE (s)-[r:TRAJTOHET_ME]->(b) SET r.rendi = n", id=bid, per=per)
        _ruaj_ne_json(i_ri={"barna": barna, "simptomat": per})
        chatbot._te_gjitha_barnat.cache_clear()
        return JSONResponse({"ok": True})

    @vetem_admin
    async def backup_info(request, l):
        te_fundit = []
        if backup.DOSJA_BACKUP.exists():
            te_fundit = [x.name for x in sorted((x for x in backup.DOSJA_BACKUP.iterdir() if x.is_dir()), reverse=True)[:8]]
        return JSONResponse({"dosja": str(backup.DOSJA_BACKUP), "te_fundit": te_fundit,
                             "lidhja": menyra_lidhjes().upper(), "ka_lokal": backup.ka_lokal()})

    @vetem_admin
    async def backup_bej(request, l):
        dosja = await run_in_threadpool(backup.ruaj_backup)
        return JSONResponse({"dosja": str(dosja)})

    return [
        Route("/api/admin/permbledhje", permbledhje),
        Route("/api/admin/perdoruesit", perdoruesit),
        Route("/api/admin/perdoruesit", perdorues_krijo, methods=["POST"]),
        Route("/api/admin/perdoruesit/{u}", perdorues_ndrysho, methods=["PATCH"]),
        Route("/api/admin/perdoruesit/{u}", perdorues_fshi, methods=["DELETE"]),
        Route("/api/admin/perdoruesit/{u}/bisedat", perdorues_bisedat),
        Route("/api/admin/barnat", barnat),
        Route("/api/admin/barnat", barna_shto, methods=["POST"]),
        Route("/api/admin/barnat/{bid}", barna_ndrysho, methods=["PATCH"]),
        Route("/api/admin/backup", backup_info),
        Route("/api/admin/backup", backup_bej, methods=["POST"]),
    ]
