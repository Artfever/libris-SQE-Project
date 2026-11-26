"""Run full @axe-core/playwright scans with a fresh local H2 fixture."""

import argparse
import json
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "fixtures"))
from circulation import Api, seed, write_json
from verify_h2 import start_app, stop_app

PORT = 18087
BEFORE_HEADING_FIX = "e2b89dbe63bfffecefbacbc784cc7dcf057c6d0d"
ROOT = HERE.parents[2]


def load_baseline(directory):
    patch_file = directory / "js" / "borrow.js"
    patch_file.parent.mkdir()
    old_source = subprocess.check_output(
        ["git", "show", f"{BEFORE_HEADING_FIX}:backend/src/main/resources/static/js/borrow.js"],
        cwd=ROOT,
    )
    patch_file.write_bytes(old_source)
    return (f"--spring.web.resources.static-locations={directory.as_uri()}/,classpath:/static/",)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-clean", action="store_true")
    parser.add_argument("--before-heading-fix", action="store_true",
                        help="Overlay the historical borrow script without changing source or the JAR")
    args = parser.parse_args()
    if args.before_heading_fix and args.expect_clean:
        parser.error("Run the clean assertion only on the fixed screen")
    with tempfile.TemporaryDirectory(prefix="libris-axe-") as scratch:
        options = load_baseline(Path(scratch)) if args.before_heading_fix else ()
        run(args, options)


def run(args, options):
    password = secrets.token_urlsafe(24) + "Aa1!"
    process = start_app(PORT, password, extra_args=options)
    try:
        api = Api(f"http://127.0.0.1:{PORT}")
        api.login(password)
        fixture = seed(api, secrets.token_urlsafe(24) + "Aa1!")
        book = fixture["items"]["book"]["id"]
        result = subprocess.run(
            ["node", str(HERE / "scan_axe.cjs")],
            input=json.dumps({"baseURL": api.base_url, "password": password,
                              "bookId": book, "studentId": fixture["student"]["id"]}),
            capture_output=True, encoding="utf-8", check=False, timeout=120,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        evidence = json.loads(result.stdout)
        if args.before_heading_fix:
            evidence["historical_borrow_script"] = BEFORE_HEADING_FIX
        assert api.call("GET", f"/api/books/{book}")["available"] is True
        history = api.call("GET", "/api/borrow-records")
        assert history["totalElements"] == 1 and history["content"][0]["status"] == "RETURNED"
        write_json(args.output, evidence)
        counts = {report["screen"]: len(report["violations"]) for report in evidence["reports"]}
        print(counts)
        if args.expect_clean and any(counts.values()):
            raise AssertionError("Accessibility regression detected")
    finally:
        stop_app(process)


if __name__ == "__main__":
    main()
