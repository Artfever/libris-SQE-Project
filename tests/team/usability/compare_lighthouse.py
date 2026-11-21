"""Capture pre-fix Lighthouse reports, then restore and rebuild current source."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FRONTEND = ROOT / "backend/src/main/resources/static/js/borrow.js"
BEFORE_COMMIT = "e2b89dbe63bfffecefbacbc784cc7dcf057c6d0d"


def build():
    subprocess.run([str(ROOT / "backend/mvnw.cmd"), "-q", "clean", "package", "-DskipTests"],
                   cwd=ROOT / "backend", check=True)


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
        subprocess.run(["python", str(Path(__file__).with_name("run_lighthouse.py")), "before"],
                       cwd=ROOT, check=True)
    finally:
        FRONTEND.write_bytes(current)
        build()


if __name__ == "__main__":
    main()
