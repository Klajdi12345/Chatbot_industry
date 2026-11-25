# FarmaBot: ndal aplikacionin dhe databazën lokale Neo4j (Ollama lihet ndezur).
# Niset me pythonw.exe: pa dritare PowerShell/konsole; në fund tregon një njoftim të vogël.
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import psutil

ROOT = str(Path(__file__).resolve().parent).lower()
NEO4J = str(Path(ROOT) / "neo4j_local").lower()


def ndal() -> list[str]:
    ndalur = []
    for p in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
        try:
            emri = (p.info["name"] or "").lower()
            exe = (p.info["exe"] or "").lower()
            cmd = " ".join(p.info["cmdline"] or [])
            if emri == "python.exe" and exe.startswith(ROOT) and ("-m web" in cmd or "streamlit" in cmd):
                p.kill()
                ndalur.append(f"FarmaBot (PID {p.pid})")
            elif emri == "java.exe" and exe.startswith(NEO4J):
                p.kill()
                ndalur.append(f"Neo4j (PID {p.pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return ndalur


if __name__ == "__main__":
    lista = ndal()
    rrenja = tk.Tk()
    rrenja.withdraw()
    teksti = "U ndalën:\n" + "\n".join(lista) if lista else "FarmaBot nuk po punonte."
    messagebox.showinfo("FarmaBot", teksti)
    rrenja.destroy()
