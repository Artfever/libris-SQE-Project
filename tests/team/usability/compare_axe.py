"""Capture full pre-fix and post-fix axe scans with the same browser tasks."""

import subprocess
from pathlib import Path

from compare_lighthouse import ROOT, FRONTEND, BEFORE_COMMIT, build


def task(label):
    subprocess.run(["python", str(Path(__file__).with_name("run_tasks.py")), label],
                   cwd=ROOT, check=True)


def main():
    current = FRONTEND.read_bytes()
    original = subprocess.check_output(
        ["git", "show", f"{BEFORE_COMMIT}:backend/src/main/resources/static/js/borrow.js"],
        cwd=ROOT,
    )
    if current == original:
        raise RuntimeError("Current frontend matches the pre-fix revision")
    try:
        FRONTEND.write_bytes(original)
        build()
        task("before")
    finally:
        FRONTEND.write_bytes(current)
        build()
    task("after")


if __name__ == "__main__":
    main()
