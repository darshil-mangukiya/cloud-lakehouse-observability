from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_step(name: str, command: list[str]) -> None:
    print(f"\n== {name} ==")
    result = subprocess.run(command, cwd=PROJECT_ROOT, text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    run_step("smoke pipeline", [sys.executable, "-B", "pipelines/run_platform.py", "--reset"])
    run_step("unit tests", [sys.executable, "-B", "-m", "unittest", "discover", "tests"])
    run_step("platform audit", [sys.executable, "-B", "scripts/platform_audit.py"])


if __name__ == "__main__":
    main()
