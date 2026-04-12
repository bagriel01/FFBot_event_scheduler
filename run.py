import os
import sys

if ".venv" not in sys.executable.replace("\\", "/") and os.environ.get("VIRTUAL_ENV", "") == "":
    sys.stderr.write(
        "ERROR: This bot must run with the local .venv Python interpreter.\n"
        "Use `.\.venv\Scripts\python.exe .\run.py` or run `.\.venv\Scripts\Activate.ps1` first.\n"
    )
    sys.exit(1)

from app.handlers.main import main

if __name__ == "__main__":
    main()
