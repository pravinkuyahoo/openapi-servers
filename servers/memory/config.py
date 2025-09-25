import os
from pathlib import Path

_DEFAULT_FILE = "memory.json"
_ENV_PATH = os.getenv("MEMORY_FILE_PATH", _DEFAULT_FILE)

# Resolve to absolute path; if relative, place beside the tool
BASE_DIR = Path(__file__).resolve().parent
MEMORY_FILE_PATH = Path(_ENV_PATH) if Path(_ENV_PATH).is_absolute() else BASE_DIR / _ENV_PATH

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
ALLOW_CREDENTIALS = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

