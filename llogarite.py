"""Llogaritë e hyrjes (admin / përdorues) në Neo4j.

  (:Llogari {perdoruesi, hash, kripe, roli, krijuar, hyrja_fundit})-[:ESHTE]->(:Person)

Fjalëkalimet nuk ruhen kurrë si tekst: ruhet vetëm hash-i PBKDF2-SHA256 me kripë të rastësishme.
"""
import hashlib
import hmac
import os
import re
import secrets
import unicodedata

import perdoruesit as db_p
from config import ROOT, query

ROLET = ("admin", "perdorues")
_ITERACIONE = 200_000


def _hash(fjalekalimi: str, kripe: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", fjalekalimi.encode(), bytes.fromhex(kripe), _ITERACIONE).hex()


def krijo_skemen():
    query("CREATE CONSTRAINT llogari_perdoruesi IF NOT EXISTS "
          "FOR (l:Llogari) REQUIRE l.perdoruesi IS UNIQUE")


# Alfabeti shqip (36 shkronja: a b c ç d dh e ë f g gj h i j k l ll m n nj o p q r rr s sh t th u v x xh y z zh)
# përdor shkronjat latine + ç dhe ë; anglishtja shton w. Lejohen të dyja, me shkronja të mëdha ose të vogla.
SHKRONJAT = "a-zA-ZçÇëË"
RE_PERDORUESI = re.compile(rf"[{SHKRONJAT}0-9_.-]{{3,30}}")
RE_EMRI = re.compile(rf"[{SHKRONJAT}][{SHKRONJAT}' .-]{{0,49}}")
MESAZH_PERDORUESI = ("Emri i përdoruesit: 3–30 karaktere, vetëm shkronja shqipe ose angleze (përfshirë ç dhe ë), "
                     "shifra dhe _ . -  (pa hapësira)")
MESAZH_EMRI = "Emri: 1–50 karaktere, vetëm shkronja shqipe ose angleze (përfshirë ç dhe ë), hapësira, ' . -"
MIN_FJALEKALIMI = 8


def normalizo_perdoruesin(perdoruesi: str | None) -> str:
    """NFC (që 'ë' e shkruar si e + ¨ të jetë e njëjtë me 'ë'), pa hapësira anash, shkronja të vogla."""
    return unicodedata.normalize("NFC", (perdoruesi or "").strip()).lower()


def valido_emrin(emer: str | None) -> str | None:
    """Emri ose pseudonimi është opsional; nëse jepet, vetëm shkronja shqipe/angleze."""
    emer = unicodedata.normalize("NFC", (emer or "").strip())
    if emer and not RE_EMRI.fullmatch(emer):
        return MESAZH_EMRI
    return None


def valido(perdoruesi: str, fjalekalimi: str) -> str | None:
    """Kthen mesazh gabimi ose None nëse të dhënat janë në rregull."""
    if not RE_PERDORUESI.fullmatch(normalizo_perdoruesin(perdoruesi)):
        return MESAZH_PERDORUESI
    if len(fjalekalimi or "") < MIN_FJALEKALIMI:
        return f"Fjalëkalimi duhet të ketë të paktën {MIN_FJALEKALIMI} karaktere."
    if fjalekalimi.strip() != fjalekalimi or not fjalekalimi.strip():
        return "Fjalëkalimi nuk mund të fillojë ose mbarojë me hapësirë."
    return None


def ekziston(perdoruesi: str) -> bool:
    return bool(query("MATCH (l:Llogari {perdoruesi: $u}) RETURN 1 AS x", u=normalizo_perdoruesin(perdoruesi)))


def krijo_llogari(perdoruesi: str, fjalekalimi: str, roli: str = "perdorues",
                  emer: str | None = None, mosha: int | None = None) -> str:
    """Krijon llogarinë dhe profilin (:Person) që i përket. Kthen id-në e personit."""
    if roli not in ROLET:
        raise ValueError(f"Rol i panjohur: {roli}")
    if gabim := valido(perdoruesi, fjalekalimi) or valido_emrin(emer):
        raise ValueError(gabim)
    if mosha is not None and not 0 <= mosha <= 110:
        raise ValueError("Mosha duhet të jetë nga 0 deri në 110 vjeç.")
    perdoruesi = normalizo_perdoruesin(perdoruesi)
    emer = unicodedata.normalize("NFC", emer.strip()) if emer and emer.strip() else None
    if ekziston(perdoruesi):
        raise ValueError("Ky emër përdoruesi ekziston.")
    kripe = secrets.token_hex(16)
    pid = db_p.shto_person(emer or perdoruesi, mosha)
    query("MATCH (p:Person {id: $pid}) "
          "CREATE (l:Llogari {perdoruesi: $u, hash: $h, kripe: $k, roli: $r, krijuar: datetime()})"
          "-[:ESHTE]->(p)",
          pid=pid, u=perdoruesi, h=_hash(fjalekalimi, kripe), k=kripe, r=roli)
    return pid


def hyr(perdoruesi: str, fjalekalimi: str) -> dict | None:
    """Kthen {perdoruesi, roli, person_id} nëse kredencialet janë të sakta."""
    perdoruesi = normalizo_perdoruesin(perdoruesi)
    rows = query("MATCH (l:Llogari {perdoruesi: $u}) OPTIONAL MATCH (l)-[:ESHTE]->(p:Person) "
                 "RETURN l.hash AS hash, l.kripe AS kripe, l.roli AS roli, p.id AS person_id",
                 u=perdoruesi)
    if not rows:
        _hash(fjalekalimi or "x", "00" * 16)  # kohë e njëjtë edhe kur llogaria nuk ekziston
        return None
    r = rows[0]
    if not hmac.compare_digest(r["hash"], _hash(fjalekalimi or "", r["kripe"])):
        return None
    query("MATCH (l:Llogari {perdoruesi: $u}) SET l.hyrja_fundit = datetime()", u=perdoruesi)
    return {"perdoruesi": perdoruesi, "roli": r["roli"], "person_id": r["person_id"]}


def ndrysho_fjalekalimin(perdoruesi: str, i_ri: str):
    if len(i_ri or "") < MIN_FJALEKALIMI:
        raise ValueError(f"Fjalëkalimi duhet të ketë të paktën {MIN_FJALEKALIMI} karaktere.")
    kripe = secrets.token_hex(16)
    query("MATCH (l:Llogari {perdoruesi: $u}) SET l.hash = $h, l.kripe = $k",
          u=normalizo_perdoruesin(perdoruesi), h=_hash(i_ri, kripe), k=kripe)


def ndrysho_rolin(perdoruesi: str, roli: str):
    if roli not in ROLET:
        raise ValueError(f"Rol i panjohur: {roli}")
    if roli != "admin" and numri_adminave() <= 1 and roli_i(perdoruesi) == "admin":
        raise ValueError("Duhet të mbetet të paktën një admin.")
    query("MATCH (l:Llogari {perdoruesi: $u}) SET l.roli = $r", u=normalizo_perdoruesin(perdoruesi), r=roli)


def roli_i(perdoruesi: str) -> str | None:
    rows = query("MATCH (l:Llogari {perdoruesi: $u}) RETURN l.roli AS r", u=normalizo_perdoruesin(perdoruesi))
    return rows[0]["r"] if rows else None


def numri_adminave() -> int:
    return query("MATCH (l:Llogari {roli: 'admin'}) RETURN count(l) AS n")[0]["n"]


def lista_llogarive() -> list[dict]:
    return query(
        "MATCH (l:Llogari) OPTIONAL MATCH (l)-[:ESHTE]->(p:Person) "
        "OPTIONAL MATCH (p)-[:DERGOI]->(m:Mesazh) "
        "RETURN l.perdoruesi AS perdoruesi, l.roli AS roli, p.id AS person_id, p.emer AS emer, "
        "p.mosha AS mosha, count(m) AS mesazhe, toString(l.krijuar) AS krijuar, "
        "toString(l.hyrja_fundit) AS hyrja_fundit ORDER BY krijuar")


def fshi_llogari(perdoruesi: str):
    """Fshin llogarinë, profilin dhe të gjitha bisedat e saj."""
    if roli_i(perdoruesi) == "admin" and numri_adminave() <= 1:
        raise ValueError("Nuk mund të fshihet admini i fundit.")
    rows = query("MATCH (l:Llogari {perdoruesi: $u}) OPTIONAL MATCH (l)-[:ESHTE]->(p:Person) "
                 "RETURN p.id AS pid", u=normalizo_perdoruesin(perdoruesi))
    if rows and rows[0]["pid"]:
        db_p.fshi_person(rows[0]["pid"])
    query("MATCH (l:Llogari {perdoruesi: $u}) DETACH DELETE l", u=normalizo_perdoruesin(perdoruesi))


def sigurohu_per_admin() -> str | None:
    """Nëse nuk ka asnjë admin, krijon 'admin' me fjalëkalim të rastësishëm dhe e shkruan te .env.
    Kthen fjalëkalimin vetëm herën e parë që krijohet."""
    krijo_skemen()
    if numri_adminave() > 0:
        return None
    perdoruesi = os.getenv("ADMIN_USERNAME", "admin")
    fjalekalimi = os.getenv("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
    krijo_llogari(perdoruesi, fjalekalimi, roli="admin", emer="Administratori")
    env = ROOT / ".env"
    tekst = env.read_text(encoding="utf-8") if env.exists() else ""
    if "ADMIN_PASSWORD=" not in tekst:
        env.write_text(tekst.rstrip("\n") + f"\nADMIN_USERNAME={perdoruesi}\nADMIN_PASSWORD={fjalekalimi}\n",
                       encoding="utf-8")
    return fjalekalimi


if __name__ == "__main__":
    fj = sigurohu_per_admin()
    print("Admini u krijua (fjalëkalimi është te .env)." if fj else "Admini ekziston tashmë.")
