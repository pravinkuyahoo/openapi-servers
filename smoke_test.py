import json
import sys
from pathlib import Path


def main():
    sys.path.insert(0, str(Path(__file__).parent))
    from main import app, discovered  # type: ignore

    tools = [name for name, _ in discovered]
    # Dump basic info: mounted prefixes and route counts
    routes = [
        {
            "path": r.path,
            "name": getattr(r, "name", None),
        }
        for r in app.routes
    ]
    print(json.dumps({
        "mounted": tools,
        "route_count": len(routes),
        "sample_routes": routes[:10],
    }, indent=2))


if __name__ == "__main__":
    main()
