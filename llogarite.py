"""Llogaritë e hyrjes (admin / përdorues) në Neo4j.

  (:Llogari {perdoruesi, email, hash, kripe, roli, krijuar, hyrja_fundit,
             rivendos_hash, rivendos_skadon, rivendos_derguar})-[:ESHTE]->(:Person)

Hyrja pranon emrin e përdoruesit ose email-in. Rivendosja e fjalëkalimit: lidhje me token njëpërdorimësh që
skadon pas 30 minutash; në databazë ruhet vetëm hash-i SHA-256 i token-it.

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
    query("CREATE CONSTRAINT llogari_email IF NOT EXISTS FOR (l:Llogari) REQUIRE l.email IS UNIQUE")


# Alfabeti shqip (36 shkronja: a b c ç d dh e ë f g gj h i j k l ll m n nj o p q r rr s sh t th u v x xh y z zh)
# përdor shkronjat latine + ç dhe ë; anglishtja shton w. Lejohen të dyja, me shkronja të mëdha ose të vogla.
SHKRONJAT = "a-zA-ZçÇëË"
RE_PERDORUESI = re.compile(rf"[{SHKRONJAT}0-9_.-]{{3,30}}")
RE_EMRI = re.compile(rf"[{SHKRONJAT}][{SHKRONJAT}' .-]{{0,49}}")
MESAZH_PERDORUESI = ("Emri i përdoruesit: 3–30 karaktere, vetëm shkronja shqipe ose angleze (përfshirë ç dhe ë), "
                     "shifra dhe _ . -  (pa hapësira)")
MESAZH_EMRI = "Emri: 1–50 karaktere, vetëm shkronja shqipe ose angleze (përfshirë ç dhe ë), hapësira, ' . -"
MIN_FJALEKALIMI = 8
RE_EMAIL = re.compile(r"[^@\s]{1,64}@[^@\s]+\.[^@\s.]{2,}")
MESAZH_EMAIL = "Email-i nuk është i vlefshëm (p.sh. emri@gmail.com)."
SKADIMI_RIVENDOSJES_MIN = 30


def normalizo_email(email: str | None) -> str:
    return unicodedata.normalize("NFC", (email or "").strip()).lower()


def valido_email(email: str | None) -> str | None:
    e = normalizo_email(email)
    return None if len(e) <= 254 and RE_EMAIL.fullmatch(e) else MESAZH_EMAIL


def email_ekziston(email: str) -> bool:
    return bool(query("MATCH (l:Llogari {email: $e}) RETURN 1 AS x", e=normalizo_email(email)))


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
                  emer: str | None = None, mosha: int | None = None, email: str | None = None) -> str:
    """Krijon llogarinë dhe profilin (:Person) që i përket. Kthen id-në e personit."""
    if roli not in ROLET:
        raise ValueError(f"Rol i panjohur: {roli}")
    if gabim := valido(perdoruesi, fjalekalimi) or valido_emrin(emer):
        raise ValueError(gabim)
    if mosha is not None and not 0 <= mosha <= 110:
        raise ValueError("Mosha duhet të jetë nga 0 deri në 110 vjeç.")
    perdoruesi = normalizo_perdoruesin(perdoruesi)
    emer = unicodedata.normalize("NFC", emer.strip()) if emer and emer.strip() else None
    if email is not None and email.strip():
        if gabim := valido_email(email):
            raise ValueError(gabim)
        email = normalizo_email(email)
        if email_ekziston(email):
            raise ValueError("Ky email është përdorur nga një llogari tjetër.")
    else:
        email = None
    if ekziston(perdoruesi):
        raise ValueError("Ky emër përdoruesi ekziston.")
    kripe = secrets.token_hex(16)
    pid = db_p.shto_person(emer or perdoruesi, mosha)
    query("MATCH (p:Person {id: $pid}) "
          "CREATE (l:Llogari {perdoruesi: $u, email: $e, hash: $h, kripe: $k, roli: $r, krijuar: datetime()})"
          "-[:ESHTE]->(p)",
          pid=pid, u=perdoruesi, e=email, h=_hash(fjalekalimi, kripe), k=kripe, r=roli)
    return pid


def hyr(perdoruesi: str, fjalekalimi: str) -> dict | None:
    """Kthen {perdoruesi, roli, person_id} nëse kredencialet janë të sakta.
    `perdoruesi` mund të jetë emri i përdoruesit ose email-i."""
    if "@" in (perdoruesi or ""):
        rows = query("MATCH (l:Llogari {email: $e}) RETURN l.perdoruesi AS u", e=normalizo_email(perdoruesi))
        perdoruesi = rows[0]["u"] if rows else ""
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


def vendos_email(perdoruesi: str, email: str | None):
    """Shton, ndryshon ose heq (email bosh) email-in e llogarisë."""
    perdoruesi = normalizo_perdoruesin(perdoruesi)
    if email and email.strip():
        if gabim := valido_email(email):
            raise ValueError(gabim)
        email = normalizo_email(email)
        if query("MATCH (l:Llogari {email: $e}) WHERE l.perdoruesi <> $u RETURN 1 AS x", e=email, u=perdoruesi):
            raise ValueError("Ky email është përdorur nga një llogari tjetër.")
    else:
        email = None
    query("MATCH (l:Llogari {perdoruesi: $u}) SET l.email = $e", u=perdoruesi, e=email)


def email_i(perdoruesi: str) -> str | None:
    rows = query("MATCH (l:Llogari {perdoruesi: $u}) RETURN l.email AS e", u=normalizo_perdoruesin(perdoruesi))
    return rows[0]["e"] if rows else None


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def krijo_rivendosje(email: str) -> dict | None:
    """Token rivendosjeje për llogarinë me këtë email: {perdoruesi, email, token}, ose None kur email-i
    nuk ekziston ose kur është kërkuar një lidhje tjetër më pak se 60 sekonda më parë."""
    email = normalizo_email(email)
    rows = query("MATCH (l:Llogari {email: $e}) "
                 "RETURN l.perdoruesi AS u, coalesce(l.rivendos_derguar > datetime() - duration({seconds: 60}), false) "
                 "AS shpejt", e=email)
    if not rows or rows[0]["shpejt"]:
        return None
    token = secrets.token_urlsafe(32)
    query("MATCH (l:Llogari {email: $e}) SET l.rivendos_hash = $h, l.rivendos_derguar = datetime(), "
          "l.rivendos_skadon = datetime() + duration({minutes: $m})",
          e=email, h=_hash_token(token), m=SKADIMI_RIVENDOSJES_MIN)
    return {"perdoruesi": rows[0]["u"], "email": email, "token": token}


def rivendos_fjalekalimin(token: str, i_ri: str) -> str:
    """Vendos fjalëkalimin e ri me token-in e email-it. Kthen emrin e përdoruesit; ValueError kur s'vlen."""
    rows = query("MATCH (l:Llogari {rivendos_hash: $h}) WHERE l.rivendos_skadon > datetime() "
                 "RETURN l.perdoruesi AS u", h=_hash_token(token or ""))
    if not rows:
        raise ValueError("Lidhja e rivendosjes nuk vlen më ose ka skaduar. Kërko një lidhje të re.")
    if len(i_ri or "") < MIN_FJALEKALIMI:
        raise ValueError(f"Fjalëkalimi duhet të ketë të paktën {MIN_FJALEKALIMI} karaktere.")
    if i_ri.strip() != i_ri:
        raise ValueError("Fjalëkalimi nuk mund të fillojë ose mbarojë me hapësirë.")
    u = rows[0]["u"]
    ndrysho_fjalekalimin(u, i_ri)
    query("MATCH (l:Llogari {perdoruesi: $u}) REMOVE l.rivendos_hash, l.rivendos_skadon", u=u)
    return u


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
        "RETURN l.perdoruesi AS perdoruesi, l.email AS email, l.roli AS roli, p.id AS person_id, p.emer AS emer, "
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
