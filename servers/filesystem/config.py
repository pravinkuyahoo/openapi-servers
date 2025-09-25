import os
import pathlib

# Constants
# You can override allowed directories via env var:
#  - ALLOWED_DIRECTORIES (comma/semicolon/pipe separated)
#  - FILESYSTEM_ALLOWED_DIRECTORIES (alias)


def _parse_allowed_dirs(val: str) -> list[str]:
    seps = [",", ";", "|"]
    parts = [val]
    for s in seps:
        parts = [p for chunk in parts for p in chunk.split(s)]
    results: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        expanded = os.path.expandvars(os.path.expanduser(p))
        try:
            results.append(str(pathlib.Path(expanded).resolve()))
        except Exception:
            # Skip invalid paths
            continue
    return results


_DEFAULT_ALLOWED = str(pathlib.Path(os.path.expanduser("~/tmp")).resolve())
_ENV_DIRS = os.getenv("ALLOWED_DIRECTORIES") or os.getenv(
    "FILESYSTEM_ALLOWED_DIRECTORIES"
)

if _ENV_DIRS:
    parsed = _parse_allowed_dirs(_ENV_DIRS)
    ALLOWED_DIRECTORIES = parsed if parsed else [_DEFAULT_ALLOWED]
else:
    ALLOWED_DIRECTORIES = [_DEFAULT_ALLOWED]

