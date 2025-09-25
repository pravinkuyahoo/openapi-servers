#!/usr/bin/env python3
"""
Install all tool requirements under openapi-servers/servers.

Usage examples:
  python openapi-servers/install_all_requirements.py
  python openapi-servers/install_all_requirements.py --upgrade
  tools_env\Scripts\python.exe openapi-servers\install_all_requirements.py

Notes:
- Re-executes itself inside openapi-servers/tools_env and runs pip with that interpreter.
- Changes working directory to each tool folder so relative includes in
  requirements files (e.g., "-r local.txt") work as expected.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


TOOLS_ENV_DIR = Path(__file__).resolve().parent / "tools_env"


def ensure_tools_env() -> None:
    try:
        expected_dir = TOOLS_ENV_DIR.resolve(strict=True)
    except FileNotFoundError:
        print(f"Expected tools_env virtual environment at {TOOLS_ENV_DIR}, but it was not found.", file=sys.stderr)
        print("Create the environment before installing requirements.", file=sys.stderr)
        raise SystemExit(1)

    current_prefix = Path(sys.prefix).resolve()
    if current_prefix == expected_dir:
        return

    if sys.platform == "win32":
        candidates = [expected_dir / "Scripts" / "python.exe"]
    else:
        candidates = [
            expected_dir / "bin" / "python3",
            expected_dir / "bin" / "python",
        ]

    for candidate in candidates:
        if candidate.exists():
            print(f"Re-running inside tools_env using {candidate}")
            os.execv(str(candidate), [str(candidate), *sys.argv])

    print(f"Unable to locate a Python interpreter inside {TOOLS_ENV_DIR} to run installs.", file=sys.stderr)
    raise SystemExit(1)

def find_requirements(servers_dir: Path) -> List[Path]:
    reqs: List[Path] = []
    for tool_dir in sorted(p for p in servers_dir.iterdir() if p.is_dir()):
        req = tool_dir / "requirements.txt"
        if req.exists():
            reqs.append(req)
    return reqs


def run_install(req_path: Path, upgrade: bool = False, quiet: bool = False) -> int:
    tool_dir = req_path.parent
    cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    if upgrade:
        cmd.append("--upgrade")
    if quiet:
        cmd.append("-q")

    print(f"\n=== Installing for {tool_dir.name} ===")
    print(f"Working dir: {tool_dir}")
    print(f"Command: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(tool_dir))
    return proc.returncode


def main(argv: List[str] | None = None) -> int:
    ensure_tools_env()
    parser = argparse.ArgumentParser(description="Install all tool requirements")
    parser.add_argument(
        "--servers-dir",
        default=str(Path(__file__).resolve().parent / "servers"),
        help="Path to the servers directory (default: %(default)s)",
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Pass --upgrade to pip install",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Pass -q to pip install",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure",
    )

    args = parser.parse_args(argv)
    servers_dir = Path(args.servers_dir).resolve()

    if not servers_dir.exists():
        print(f"Servers directory not found: {servers_dir}", file=sys.stderr)
        return 2

    req_files = find_requirements(servers_dir)
    if not req_files:
        print("No requirements.txt files found.")
        return 0

    successes: List[Tuple[str, Path]] = []
    failures: List[Tuple[str, Path, int]] = []

    print(f"Discovered {len(req_files)} requirement files under {servers_dir}:")
    for req in req_files:
        print(f" - {req}")

    for req in req_files:
        rc = run_install(req, upgrade=args.upgrade, quiet=args.quiet)
        if rc == 0:
            successes.append((req.parent.name, req))
        else:
            failures.append((req.parent.name, req, rc))
            print(f"Install failed for {req.parent.name} (exit {rc})", file=sys.stderr)
            if args.fail_fast:
                break

    print("\n=== Summary ===")
    print(f"Succeeded: {len(successes)}")
    for name, req in successes:
        print(f"  - {name}: {req}")
    print(f"Failed: {len(failures)}")
    for name, req, rc in failures:
        print(f"  - {name}: {req} (exit {rc})")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

