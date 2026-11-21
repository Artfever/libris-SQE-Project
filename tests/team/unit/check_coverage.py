"""Enforce scoped team coverage floors from a JaCoCo XML report."""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FLOORS = {
    "com/example/lms/service/BorrowRecordService": {"LINE": 0.98, "BRANCH": 0.97},
    "com/example/lms/util/OverdueCalculator": {"LINE": 1.0, "BRANCH": 1.0},
}


def verify(report: Path) -> list[str]:
    root = ET.parse(report).getroot()
    classes = {node.attrib["name"]: node for node in root.findall(".//class")}
    errors = []
    for class_name, counters in FLOORS.items():
        node = classes.get(class_name)
        if node is None:
            errors.append(f"Missing JaCoCo class: {class_name}")
            continue
        observed = {counter.attrib["type"]: counter.attrib for counter in node.findall("counter")}
        for kind, minimum in counters.items():
            counter = observed.get(kind)
            if counter is None:
                errors.append(f"Missing {kind} counter for {class_name}")
                continue
            covered, missed = int(counter["covered"]), int(counter["missed"])
            total = covered + missed
            ratio = covered / total if total else 1.0
            print(f"{class_name} {kind}: {covered}/{total} ({ratio:.1%}); floor {minimum:.0%}")
            if ratio < minimum:
                errors.append(f"{class_name} {kind} {ratio:.1%} is below {minimum:.0%}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    if not args.report.is_file():
        print(f"JaCoCo report not found: {args.report}", file=sys.stderr)
        return 2
    errors = verify(args.report)
    if errors:
        print("Team coverage gate failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Team coverage gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
