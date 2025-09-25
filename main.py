from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
import logging
import os
import sys
from pathlib import Path
import importlib.util
from typing import List, Tuple
from dotenv import load_dotenv

load_dotenv()



def _resolve_log_level(name: str | None) -> int:
    if not name:
        return logging.INFO
    return getattr(logging, name.upper(), logging.INFO)


LOG_LEVEL = _resolve_log_level(
    os.getenv("UNIFIED_TOOLS_LOG_LEVEL", os.getenv("LOG_LEVEL", "INFO"))
)
logger = logging.getLogger("unified_tools")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)
logger.propagate = False
logger.debug("Logger initialized at level %s", logging.getLevelName(LOG_LEVEL))

api_key = os.getenv("API_KEY")
logger.debug("API key configured: %s", bool(api_key))


BASE_DIR = Path(__file__).resolve().parent
SERVERS_DIR = BASE_DIR / "servers"
logger.debug("Base directory set to %s", BASE_DIR)
logger.debug("Servers directory resolved to %s", SERVERS_DIR)


def _sanitize(name: str) -> str:
    return "".join(c if (c.isalnum() or c == "_") else "_" for c in name)


def _load_tool_as_package(tool_dir: Path, package_name: str):
    """Load a tool directory as a package and return its main module.
    Expects tool_dir to contain __init__.py and main.py
    """
    init_file = tool_dir / "__init__.py"
    main_file = tool_dir / "main.py"
    if not init_file.exists() or not main_file.exists():
        return None

    pkg_spec = importlib.util.spec_from_file_location(
        package_name, str(init_file), submodule_search_locations=[str(tool_dir)]
    )
    if pkg_spec is None or pkg_spec.loader is None:
        return None
    pkg_module = importlib.util.module_from_spec(pkg_spec)
    sys.modules[package_name] = pkg_module
    pkg_spec.loader.exec_module(pkg_module)

    main_spec = importlib.util.spec_from_file_location(
        f"{package_name}.main", str(main_file)
    )
    if main_spec is None or main_spec.loader is None:
        return None
    main_module = importlib.util.module_from_spec(main_spec)
    sys.modules[f"{package_name}.main"] = main_module
    main_spec.loader.exec_module(main_module)
    return main_module


def _load_tool_as_module(tool_dir: Path, module_name: str):
    """Load a tool main.py directly as a module and return it."""
    main_file = tool_dir / "main.py"
    if not main_file.exists():
        return None
    spec = importlib.util.spec_from_file_location(module_name, str(main_file))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def discover_tools() -> List[Tuple[str, object]]:
    """Discover tools under servers/, load their app, and return list of (prefix, app)."""
    logger.debug("Starting tool discovery in %s", SERVERS_DIR)
    results: List[Tuple[str, object]] = []
    for tool_dir in sorted(p for p in SERVERS_DIR.iterdir() if p.is_dir()):
        logger.debug("Inspecting tool directory %s", tool_dir)
        main_py = tool_dir / "main.py"
        if not main_py.exists():
            logger.debug("Skipping %s: main.py not found", tool_dir.name)
            continue

        prefix = f"/{tool_dir.name}"
        sanitized = _sanitize(tool_dir.name)

        use_package = (tool_dir / "__init__.py").exists()
        if not use_package:
            try:
                content = main_py.read_text(encoding="utf-8", errors="ignore")
                if "from ." in content or "import ." in content:
                    use_package = True
            except Exception:
                logger.debug("Unable to inspect %s for relative imports", tool_dir.name)

        logger.debug(
            "Loading %s as %s", tool_dir.name, "package" if use_package else "module"
        )
        module = None
        try:
            if use_package:
                module = _load_tool_as_package(tool_dir, f"agg_{sanitized}")
            else:
                module = _load_tool_as_module(tool_dir, f"tool_{sanitized}_main")
        except Exception:
            logger.exception("Skipping %s due to import error", tool_dir.name)
            continue

        if module is None:
            logger.debug("Module for %s returned None; skipping", tool_dir.name)
            continue

        app_obj = getattr(module, "app", None)
        if app_obj is None:
            logger.warning("Skipping %s: no 'app' found in main.py", tool_dir.name)
            continue

        logger.debug("Discovered tool '%s' mounted at %s", tool_dir.name, prefix)
        results.append((prefix, app_obj))

    logger.info("Discovered %d tool(s)", len(results))
    return results


app = FastAPI(
    title="Unified Tools API",
    version="1.0.0",
    description="Single FastAPI server mounting all tool apps under /<tool-dir>",
)
logger.debug("FastAPI application instantiated")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.debug("CORS middleware configured")


# Include each tool's router under a prefix so all endpoints live in one OpenAPI
discovered = discover_tools()
for prefix, sub_app in discovered:
    try:
        app.include_router(sub_app.router, prefix=prefix, tags=[prefix.strip("/")])
        logger.debug("Mounted router for prefix %s", prefix)
    except Exception:
        logger.exception("Failed to include router for %s", prefix)


@app.get("/")
def index():
    logger.debug("Index endpoint invoked")
    return {
        "message": "Unified Tools API",
        "tools": [
            {
                "name": prefix.strip("/"),
                "base_url": prefix,
                "docs": "/docs",
                "openapi": "/openapi.json",
            }
            for (prefix, _) in discovered
        ],
    }


@app.get("/openapi-merged.json", response_class=JSONResponse)
def openapi_merged():
    logger.debug("openapi-merged endpoint requested")
    return app.openapi()


@app.get("/openapi.json", response_class=JSONResponse)
def openapi():
    logger.debug("openapi endpoint requested")
    return app.openapi()


@app.get("/docs", response_class=HTMLResponse)
def docs():
    logger.debug("docs endpoint requested")
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Unified Tools API - Docs")


@app.get("/docs-merged", response_class=HTMLResponse)
def docs_merged():
    logger.debug("docs-merged endpoint requested")
    return get_swagger_ui_html(openapi_url="/openapi-merged.json", title="Unified Tools API - Docs (Merged)")


@app.get("/redoc", response_class=HTMLResponse)
def redoc():
    logger.debug("redoc endpoint requested")
    return get_redoc_html(openapi_url="/openapi.json", title="Unified Tools API - ReDoc")


@app.get("/redoc-merged", response_class=HTMLResponse)
def redoc_merged():
    logger.debug("redoc-merged endpoint requested")
    return get_redoc_html(openapi_url="/openapi-merged.json", title="Unified Tools API - ReDoc (Merged)")


@app.get("/health")
def health():
    logger.debug("health endpoint requested")
    return {"status": "ok"}


@app.get("/time")
def time():
    import time as _time

    logger.debug("time endpoint requested")
    return {"time": _time.time()}


# Ensure unique operationIds across all included routers (helps OpenAPI clients)
_cached_openapi = None


def custom_openapi():
    global _cached_openapi
    if _cached_openapi:
        logger.debug("Returning cached OpenAPI schema")
        return _cached_openapi

    logger.debug("Generating OpenAPI schema")
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    paths = schema.get("paths", {})
    logger.debug("Processing %d path entries for operationId prefixing", len(paths))
    for path, item in list(paths.items()):
        seg = path.split("/", 2)[1] if path.startswith("/") and len(path.split("/")) > 1 else "root"
        for method, op in (item or {}).items():
            if isinstance(op, dict) and op.get("operationId"):
                op["operationId"] = f"{seg}__{op['operationId']}"

    _cached_openapi = schema
    logger.debug("OpenAPI schema cached")
    return _cached_openapi


app.openapi = custom_openapi  # type: ignore
