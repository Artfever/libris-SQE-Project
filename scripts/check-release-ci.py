"""Check that the exact release revision passed the complete Libris CI workflow."""

import argparse
import json
import re
import urllib.parse
import urllib.request

BASE = "https://api.github.com/repos/Artfever/libris-SQE-Project/actions"
REQUIRED = {"build", "maven", "team-tests", "mutation", "sonarqube",
            "javascript", "phase5", "backup-script", "docker-build"}


def get(path, **parameters):
    url = BASE + path + "?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision", help="Full Git SHA of the reviewed release")
    args = parser.parse_args()
    sha = args.revision.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        parser.error("Supply the full 40-character revision")
    try:
        runs = get("/workflows/ci.yml/runs", branch="main", event="push", head_sha=sha)["workflow_runs"]
        if not runs:
            raise ValueError("No main push run exists for the release revision")
        run = runs[0]
        if (run["head_sha"], run["status"], run["conclusion"]) != (sha, "completed", "success"):
            raise ValueError(f"Latest run did not pass: {run['html_url']}")
        jobs = get(f"/runs/{run['id']}/jobs", filter="latest", per_page=100)["jobs"]
        passed = {job["name"] for job in jobs if job["conclusion"] == "success"}
        if missing := REQUIRED - passed:
            raise ValueError("Missing or unsuccessful release checks: " + ", ".join(sorted(missing)))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Release blocked: {error}\n")
    print(f"Release CI passed for {sha}: {run['html_url']}")


if __name__ == "__main__":
    main()
