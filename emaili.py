"""Dërgimi i email-eve (rivendosja e fjalëkalimit) me SMTP.

Konfigurimi te .env, p.sh. me Gmail (kërkon "App password", jo fjalëkalimin e zakonshëm):
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=adresa.juaj@gmail.com
  SMTP_PASSWORD=xxxx xxxx xxxx xxxx
  SMTP_FROM=FarmaBot <adresa.juaj@gmail.com>     (opsionale)
  FARMABOT_URL=http://localhost:8501              (adresa që del te lidhja e email-it)

Pa SMTP të konfiguruar, email-i nuk dërgohet: shkruhet te logs/emailet.log (për prova në këtë kompjuter).
"""
import logging
import os
import smtplib
import ssl
import time
from email.message import EmailMessage

from config import ROOT

log = logging.getLogger("farmabot.email")


def eshte_konfiguruar() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"))


def adresa_aplikacionit() -> str:
    return os.getenv("FARMABOT_URL", "http://localhost:8501").rstrip("/")


def dergo(per: str, subjekti: str, tekst: str, html: str | None = None) -> bool:
    """Dërgon email-in. Kthen True nëse u dërgua me SMTP, False nëse u shkrua vetëm te log-u."""
    msg = EmailMessage()
    msg["To"] = per
    msg["Subject"] = subjekti
    msg["From"] = os.getenv("SMTP_FROM") or f"FarmaBot <{os.getenv('SMTP_USER', 'farmabot@localhost')}>"
    msg.set_content(tekst)
    if html:
        msg.add_alternative(html, subtype="html")

    if not eshte_konfiguruar():
        dosja = ROOT / "logs"
        dosja.mkdir(exist_ok=True)
        with open(dosja / "emailet.log", "a", encoding="utf-8") as f:
            f.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} · Për: {per} · {subjekti}\n{tekst}\n")
        log.warning("SMTP nuk është konfiguruar: email-i për %s u shkrua te logs/emailet.log", per)
        return False

    host, port = os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587"))
    konteksti = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=konteksti, timeout=20) as s:
            s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.starttls(context=konteksti)
            s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            s.send_message(msg)
    return True


def email_rivendosjeje(per: str, perdoruesi: str, token: str, gjuha: str = "sq") -> bool:
    lidhja = f"{adresa_aplikacionit()}/#/rivendos/{token}"
    if gjuha == "en":
        subjekti = "FarmaBot: reset your password"
        tekst = (f"Hello {perdoruesi},\n\nWe received a request to reset your FarmaBot password.\n"
                 f"Open this link within 30 minutes to choose a new password:\n\n{lidhja}\n\n"
                 "If you did not ask for this, ignore this email: your password stays the same.\n")
        butoni, hyrja, fundi = "Choose a new password", f"Hello {perdoruesi}, we received a request to reset your FarmaBot password. The link is valid for 30 minutes.", "If you did not ask for this, ignore this email: your password stays the same."
    else:
        subjekti = "FarmaBot: rivendos fjalëkalimin"
        tekst = (f"Përshëndetje {perdoruesi},\n\nMorëm një kërkesë për të rivendosur fjalëkalimin e FarmaBot-it.\n"
                 f"Hap këtë lidhje brenda 30 minutave dhe zgjidh një fjalëkalim të ri:\n\n{lidhja}\n\n"
                 "Nëse nuk e ke kërkuar ti, injoroje këtë email: fjalëkalimi yt nuk ndryshon.\n")
        butoni, hyrja, fundi = "Zgjidh fjalëkalimin e ri", f"Përshëndetje {perdoruesi}, morëm një kërkesë për të rivendosur fjalëkalimin e FarmaBot-it. Lidhja vlen 30 minuta.", "Nëse nuk e ke kërkuar ti, injoroje këtë email: fjalëkalimi yt nuk ndryshon."
    html = f"""<div style="font-family:Segoe UI,Arial,sans-serif;max-width:480px;margin:auto;padding:24px;color:#0d0d0d">
<h2 style="margin:0 0 12px;font-weight:600">FarmaBot</h2><p style="line-height:1.55">{hyrja}</p>
<p style="margin:24px 0"><a href="{lidhja}" style="background:#0d0d0d;color:#fff;padding:12px 20px;border-radius:999px;
text-decoration:none;font-weight:600">{butoni}</a></p>
<p style="color:#5d5d5d;font-size:13px;line-height:1.5">{fundi}</p>
<p style="color:#8f8f8f;font-size:12px;word-break:break-all">{lidhja}</p></div>"""
    return dergo(per, subjekti, tekst, html)
