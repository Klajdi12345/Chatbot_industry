"""Test i shpejtë nga terminali:  python testo.py"""
from chatbot import Profili, gjej_simptomat, kontrollo_urgjencen, pergjigju

RASTET = [
    ("me dhemb dhembi", Profili(mosha=30)),
    ("kam temperature dhe me dhemb koka", Profili(mosha=28, gjendjet={"shtatzeni"})),
    ("me dhemb barku nga cikli", Profili(mosha=22, gjendjet={"ulcer"})),
    ("kolle e thate qe 3 dite", Profili(mosha=40, gjendjet={"antidepresive"})),
    ("teshtij shume dhe me lotojne syte", Profili(mosha=8)),
    ("kam dhimbje gjoksi qe shtrihet ne krah", Profili(mosha=60)),
]

if __name__ == "__main__":
    print("== Kërkimi i simptomave ==")
    for tekst, _ in RASTET:
        s = gjej_simptomat(tekst)
        print(f"{tekst!r:45} → {[(x['emer'], round(x['score'], 3)) for x in s]}"
              f"{'  [URGJENCË]' if kontrollo_urgjencen(tekst) else ''}")
    print("\n== Përgjigje të plota ==")
    for tekst, profili in RASTET:
        p = pergjigju(tekst, [], profili)
        print(f"\n### {tekst}  (mosha {profili.mosha}, {sorted(profili.gjendjet)})")
        print("Barna:", [b["emer"] for b in p.barnat])
        print("Përjashtuara:", [x["emer"] for x in p.te_perjashtuara])
        print(p.tekst)
