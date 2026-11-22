"""Nis FarmaBot Web:   python -m web   (http://localhost:8501, vetëm në këtë kompjuter)."""
import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run("web.server:app", host=os.getenv("FARMABOT_HOST", "127.0.0.1"),
                port=int(os.getenv("FARMABOT_PORT", "8501")), log_level="info")
