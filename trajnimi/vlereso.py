"""Vlerësimi i saktësisë së FarmaBot-it me grupin trajnimi/rastet.json.

    python -m trajnimi.vlereso            → raport te trajnimi/raportet/ dhe përmbledhje në ekran
    python -m trajnimi.vlereso --gabimet  → shfaq edhe çdo rast të gabuar
    python -m trajnimi.vlereso --gjykatesi [N] → edhe gjykatësi (gemma3:4b) lexon N përgjigje (shiko gjykatesi.py)

Çfarë matet:
  simptome / anglisht  bota gjen simptomën e duhur (ose, të paktën, e pyet personin mes kandidatëve)
  urgjence             çdo urgjencë kapet (duhet 100%)
  jo_urgjence          simptomat e lehta nuk trajtohen si urgjencë
  siguria              asnjë ilaç i kundërindikuar për profilin nuk sugjerohet (duhet 0 shkelje)
  femije               për fëmijët nuk jepen doza të rriturish
  pa_lidhje            pyetjet pa lidhje me shëndetin nuk marrin ilaçe
  biseda               pyetjet vijuese kuptohen (doza, alternativa, këshilla, mjeku...)
  kontroll_*           grup i pavarur që NUK përdoret për rregullime: mat saktësinë e vërtetë te mesazhe të reja

Përgjigjet gjenerohen pa modelin gjuhësor (mendo=False, gjuha="sq"), që vlerësimi të jetë i shpejtë dhe i
përsëritshëm; kuptimi i anglishtes testohet njësoj, sepse bota e kthen anglishten në shqip para kërkimit.
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

DOSJA = Path(__file__).parent
RAPORTET = DOSJA / "raportet"

EMRAT = {"simptome": "Simptomat (shqip)", "anglisht": "Simptomat (anglisht)", "urgjence": "Urgjencat",
         "jo_urgjence": "Pa alarm të rremë", "siguria": "Siguria e ilaçeve", "femije": "Fëmijët pa doza të rriturish",
         "pa_lidhje": "Pyetje pa lidhje", "biseda": "Pyetjet vijuese",
         "kontroll_simptome": "Kontroll i pavarur: simptomat", "kontroll_urgjence": "Kontroll i pavarur: urgjencat"}
# Kufijtë minimalë: nën to vlerësimi quhet i dështuar (urgjencat dhe siguria nuk lejojnë asnjë gabim).
KUFIJTE = {"urgjence": 1.0, "siguria": 1.0, "femije": 1.0, "simptome": 0.85, "anglisht": 0.8,
           "jo_urgjence": 0.8, "pa_lidhje": 0.8, "biseda": 0.85, "kontroll_simptome": 0.8, "kontroll_urgjence": 1.0}


def _biseda(mesazhet: list[str], profili=None):
    """Kalon mesazhet njëri pas tjetrit me kontekstin e bisedës (si serveri web). Kthen përgjigjen e fundit."""
    from chatbot import Konteksti, Profili, pergjigju
    profili = profili or Profili()
    historia, k = [], {}
    p = None
    for m in mesazhet:
        kont = Konteksti(simptomat=k.get("simptomat", []), barnat=k.get("barnat", []),
                         pritje=k.get("pritje", []), pritje_shto=k.get("pritje_shto", False))
        p = pergjigju(m, historia, profili, konteksti=kont, mendo=False, gjuha="sq")
        if p.simptomat:
            k["simptomat"] = [s["id"] for s in p.simptomat]
        if p.barnat_konteksti:
            k["barnat"] = p.barnat_konteksti
        if not p.urgjence:
            k["pritje"], k["pritje_shto"] = p.pritje, p.pritje_shto
        if p.gjendje_te_reja:
            profili.gjendjet |= p.gjendje_te_reja
        historia += [{"role": "user", "content": m}, {"role": "assistant", "content": p.tekst}]
    return p


def _ids(lista) -> list[str]:
    return [x["id"] if isinstance(x, dict) else x for x in lista or []]


def vlereso(on_progres=None, kategorite: list[str] | None = None) -> dict:
    """Ekzekuton të gjitha rastet. on_progres(i, gjithsej, kategoria) thirret pas çdo rasti."""
    from chatbot import Profili
    rastet = json.loads((DOSJA / "rastet.json").read_text(encoding="utf-8"))
    pune = []
    for kat in EMRAT:
        if kategorite and kat not in kategorite:
            continue
        for r in rastet.get(kat, []):
            pune.append((kat, r))
    rezultatet, fillimi = [], time.perf_counter()
    for i, (kat, r) in enumerate(pune, 1):
        t0 = time.perf_counter()
        try:
            if kat in ("simptome", "anglisht", "kontroll_simptome"):
                mesazh, pritet = r
                p = _biseda([mesazh])
                gjetur, pyeti = _ids(p.simptomat), _ids(p.pritje)
                ok = set(pritet) <= set(gjetur)
                rez = {"mesazh": mesazh, "pritet": pritet, "gjetur": gjetur, "pyeti": pyeti,
                       "statusi": "sakte" if ok else ("pyeti" if set(pritet) <= set(gjetur) | set(pyeti) else "gabim")}
            elif kat in ("urgjence", "kontroll_urgjence"):
                p = _biseda([r])
                rez = {"mesazh": r, "pritet": "urgjencë", "gjetur": "urgjencë" if p.urgjence else p.qellimi,
                       "statusi": "sakte" if p.urgjence else "gabim"}
            elif kat == "jo_urgjence":
                p = _biseda([r])
                rez = {"mesazh": r, "pritet": "pa urgjencë", "gjetur": "urgjencë" if p.urgjence else p.qellimi,
                       "statusi": "gabim" if p.urgjence else "sakte"}
            elif kat == "siguria":
                prof = Profili(mosha=r["profili"].get("mosha"), gjendjet=set(r["profili"].get("gjendjet", [])))
                p = _biseda([r["mesazh"]], prof)
                barnat = _ids(p.barnat)
                shkelje = sorted(set(barnat) & set(r["ndalohen"]))
                rez = {"mesazh": r["mesazh"], "profili": r["profili"], "pritet": f"pa {', '.join(r['ndalohen']) or '—'}",
                       "gjetur": barnat, "statusi": "gabim" if shkelje else "sakte", "shkelje": shkelje}
            elif kat == "femije":
                mesazh, pa_doza = r
                p = _biseda([mesazh])
                rez = {"mesazh": mesazh, "pritet": "pa doza" if pa_doza else "me doza",
                       "gjetur": "pa doza" if p.pa_doza else "me doza", "statusi": "sakte" if p.pa_doza == pa_doza else "gabim"}
            elif kat == "pa_lidhje":
                p = _biseda([r])
                rez = {"mesazh": r, "pritet": "pa ilaçe", "gjetur": _ids(p.barnat) or _ids(p.simptomat) or p.qellimi,
                       "statusi": "gabim" if (p.barnat or p.simptomat) else "sakte"}
            else:  # biseda
                p = _biseda(r["mesazhet"])
                rez = {"mesazh": " → ".join(r["mesazhet"]), "pritet": r["qellimi"], "gjetur": p.qellimi,
                       "statusi": "sakte" if p.qellimi == r["qellimi"] else "gabim"}
        except Exception as e:  # noqa: BLE001 — një rast që bie nuk e ndal vlerësimin
            rez = {"mesazh": str(r)[:120], "pritet": "—", "gjetur": f"GABIM: {e}", "statusi": "gabim"}
        rez["kategoria"] = kat
        rez["sekonda"] = round(time.perf_counter() - t0, 2)
        rezultatet.append(rez)
        if on_progres:
            on_progres(i, len(pune), kat)

    permbledhje = {}
    for kat in EMRAT:
        rr = [x for x in rezultatet if x["kategoria"] == kat]
        if not rr:
            continue
        sakte = sum(x["statusi"] == "sakte" for x in rr)
        pyeti = sum(x["statusi"] == "pyeti" for x in rr)
        permbledhje[kat] = {"emri": EMRAT[kat], "gjithsej": len(rr), "sakte": sakte, "pyeti": pyeti,
                            "saktesia": round(sakte / len(rr), 4), "kufiri": KUFIJTE[kat],
                            "kaloi": sakte / len(rr) >= KUFIJTE[kat]}
    gjithsej = len(rezultatet)
    raporti = {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "sekonda": round(time.perf_counter() - fillimi, 1),
        "gjithsej": gjithsej,
        "sakte": sum(x["statusi"] == "sakte" for x in rezultatet),
        "saktesia": round(sum(x["statusi"] == "sakte" for x in rezultatet) / max(gjithsej, 1), 4),
        "kaloi": all(v["kaloi"] for v in permbledhje.values()),
        "kategorite": permbledhje,
        "gabimet": [x for x in rezultatet if x["statusi"] != "sakte"],
        "rezultatet": rezultatet,
    }
    return raporti


def ruaj(raporti: dict) -> Path:
    RAPORTET.mkdir(exist_ok=True)
    emri = RAPORTET / f"{raporti['data'].replace(':', '').replace(' ', '_')}.json"
    tekst = json.dumps(raporti, ensure_ascii=False, indent=1)
    emri.write_text(tekst, encoding="utf-8")
    (RAPORTET / "i_fundit.json").write_text(tekst, encoding="utf-8")
    return emri


def i_fundit() -> dict | None:
    f = RAPORTET / "i_fundit.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def historiku() -> list[dict]:
    """Përmbledhjet e vlerësimeve të mëparshme (më i vjetri i pari), për të parë përmirësimin."""
    out = []
    for f in sorted(RAPORTET.glob("20*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        out.append({"data": r["data"], "saktesia": r["saktesia"], "gjithsej": r["gjithsej"],
                    "kategorite": {k: v["saktesia"] for k, v in r["kategorite"].items()}})
    return out


def shtyp(raporti: dict, gabimet: bool = False):
    print(f"\nVlerësimi {raporti['data']} · {raporti['gjithsej']} raste · {raporti['sekonda']} s")
    print(f"{'Kategoria':32} {'Saktë':>9} {'Saktësia':>9} {'Kufiri':>7}")
    for v in raporti["kategorite"].values():
        shenja = "OK " if v["kaloi"] else "!! "
        pyeti = f" (+{v['pyeti']} pyeti)" if v["pyeti"] else ""
        print(f"{shenja}{v['emri']:29} {v['sakte']:>4}/{v['gjithsej']:<4} {v['saktesia']:>8.0%} {v['kufiri']:>7.0%}{pyeti}")
    print(f"\nGjithsej: {raporti['saktesia']:.1%} · {'KALOI' if raporti['kaloi'] else 'NUK KALOI'}")
    if gabimet:
        for g in raporti["gabimet"]:
            print(f"  [{g['kategoria']}] {g['mesazh']!r}: pritej {g['pritet']}, u gjet {g['gjetur']}"
                  + (f", pyeti për {g['pyeti']}" if g.get("pyeti") else ""))


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--gabimet", action="store_true", help="shfaq çdo rast të gabuar")
    a.add_argument("--kategori", nargs="*", choices=list(EMRAT), help="vetëm këto kategori")
    a.add_argument("--gjykatesi", nargs="?", type=int, const=40, metavar="N",
                   help="gjykatësi (gemma3:4b) lexon N përgjigje (parazgjedhje 40)")
    args = a.parse_args()
    r = vlereso(on_progres=lambda i, n, k: print(f"\r  {i}/{n} {k:12}", end="", flush=True), kategorite=args.kategori)
    print()
    if args.gjykatesi:
        from trajnimi import gjykatesi
        if gjykatesi.gati():
            r["gjykatesi"] = gjykatesi.gjyko_te_gjitha(
                args.gjykatesi, on_progres=lambda i, n, k: print(f"\r  gjykatësi {i}/{n} {k:12}", end="", flush=True))
            print()
        else:
            print(f"Gjykatësi u anashkalua: {gjykatesi.GJYKATESI_MODEL} nuk është i instaluar.")
    f = ruaj(r)
    shtyp(r, args.gabimet)
    if "gjykatesi" in r:
        from trajnimi import gjykatesi
        gjykatesi.shtyp(r["gjykatesi"])
    print(f"\nRaporti: {f}")
