# FarmaBot: nis gjithçka me një klikim (Ollama -> Neo4j lokal -> aplikacioni web) dhe e hap
# si faqe web në shfletuesin e zakonshëm (http://localhost:8501). Hostimi në internet bëhet në fund.
# Niset me pythonw.exe: asnjë dritare PowerShell ose konsole. Vetëm nëse ndodh një gabim
# shfaqet një njoftim i vogël.
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / "logs"
URL = "http://localhost:8501/"
NISJA = ROOT / "assets" / "nisja.html"   # faqja "FarmaBot po niset" që kalon vetë te aplikacioni
# Vetëm CREATE_NO_WINDOW (jo DETACHED_PROCESS): procesi merr një konsolë të padukshme që e trashëgojnë
# edhe proceset që ai nis vetë (Neo4j, python i venv-it). Me DETACHED_PROCESS ata hapnin dritare cmd.
PA_DRITARE = subprocess.CREATE_NO_WINDOW

def porti_hapur(porti: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", porti), timeout=1):
            return True
    except OSError:
        return False


def prit_portin(porti: int, sekonda: int, emri: str) -> None:
    fund = time.time() + sekonda
    while time.time() < fund:
        if porti_hapur(porti):
            return
        time.sleep(1)
    raise RuntimeError(f"{emri} nuk u nis brenda {sekonda} sekondave. Shiko dosjen logs\\ te projekti.")


def nis_proces(args, emri_log: str, cwd: Path, env=None) -> None:
    out = open(LOGS / f"{emri_log}.out.log", "ab")
    err = open(LOGS / f"{emri_log}.err.log", "ab")
    # Grup i ri procesesh + jashtë "job"-it të prindit: shërbimet vazhdojnë edhe pasi mbyllet nisësi.
    for flamujt in (PA_DRITARE | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_BREAKAWAY_FROM_JOB,
                    PA_DRITARE | subprocess.CREATE_NEW_PROCESS_GROUP):
        try:
            subprocess.Popen(args, cwd=str(cwd), env=env, stdout=out, stderr=err,
                             stdin=subprocess.DEVNULL, creationflags=flamujt, close_fds=True)
            return
        except OSError:
            continue
    raise RuntimeError(f"Nuk u nis {args[0]}")


def gjej_ollama() -> str:
    gjetur = shutil.which("ollama")
    if gjetur:
        return gjetur
    return str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe")


def hap_faqen(adresa: str) -> None:
    """Hap FarmaBot-in si faqe web në shfletuesin e zakonshëm të kompjuterit (skedë e re)."""
    import webbrowser
    webbrowser.open(adresa)


def nis_sherbimet() -> None:
    LOGS.mkdir(exist_ok=True)

    # 1. Ollama (modelet gjuhësore)
    if not porti_hapur(11434):
        nis_proces([gjej_ollama(), "serve"], "ollama", ROOT)

    # 2. Neo4j lokal (databaza)
    if not porti_hapur(7687):
        env = dict(os.environ, JAVA_HOME=str(ROOT / "neo4j_local" / "jre"))
        server = ROOT / "neo4j_local" / "server"
        # Java niset direkt (jo me neo4j.bat, që brenda vetes thërret PowerShell-in).
        java = ROOT / "neo4j_local" / "jre" / "bin" / "java.exe"
        nis_proces([str(java), "-cp", f"{server}/lib/*", f"-Dbasedir={server}",
                    "org.neo4j.server.startup.Neo4jCommand", "console"], "neo4j", server, env)

    prit_portin(11434, 60, "Ollama")
    prit_portin(7687, 180, "Neo4j")

    # 3. Aplikacioni FarmaBot (web: python -m web)
    if not porti_hapur(8501):
        python = ROOT / "venv_chatbot" / "Scripts" / "python.exe"
        nis_proces([str(python), "-m", "web"], "farmabot", ROOT)
        prit_portin(8501, 90, "FarmaBot")


def trego_gabimin(tekst: str) -> None:
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, f"FarmaBot nuk u nis:\n\n{tekst}", "FarmaBot", 0x10)


def main() -> None:
    if porti_hapur(8501):
        hap_faqen(URL)          # gjithçka po punon: hapet direkt
        return
    hap_faqen(NISJA.as_uri())   # faqja "po niset" hapet menjëherë dhe kalon vetë te FarmaBot-i kur të jetë gati
    try:
        nis_sherbimet()
    except Exception as e:  # noqa: BLE001 - i tregohet përdoruesit
        trego_gabimin(str(e))


if __name__ == "__main__":
    main()
