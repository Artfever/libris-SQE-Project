"""Check resolved Maven packages and versions against the OSV batch API."""

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://api.osv.dev/v1/querybatch"


def packages(node):
    result = []
    if node.get("groupId") and node.get("artifactId") and node.get("version"):
        result.append({"name": f"{node['groupId']}:{node['artifactId']}",
                       "version": node["version"], "scope": node.get("scope", "root")})
    for child in node.get("children", []):
        result.extend(packages(child))
    return result


def query(batch):
    payload = {"queries": [{"version": item["version"],
                            "package": {"name": item["name"], "ecosystem": "Maven"}}
                           for item in batch]}
    request = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)["results"]
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503) or attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("OSV request did not complete")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path, help="Maven dependency:tree JSON output")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    tree = json.loads(args.tree.read_text(encoding="utf-8"))
    unique = {(p["name"], p["version"]): p for p in packages(tree)}
    items = list(unique.values())
    findings = []
    for start in range(0, len(items), 100):
        batch = items[start:start + 100]
        results = query(batch)
        if len(results) != len(batch):
            raise AssertionError("OSV response count did not match request")
        for package, result in zip(batch, results):
            if result.get("next_page_token"):
                raise RuntimeError("OSV pagination requires review for this package")
            ids = [vulnerability["id"] for vulnerability in result.get("vulns", [])]
            if ids:
                findings.append({**package, "vulnerability_ids": ids})
    report = {"source": "resolved Maven dependency tree", "api": URL,
              "packages_checked": len(items), "packages": items, "findings": findings}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Checked {len(items)} resolved Maven packages; {len(findings)} packages have OSV IDs")


if __name__ == "__main__":
    main()
