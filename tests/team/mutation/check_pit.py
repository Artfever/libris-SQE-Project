"""Reject PIT reports with execution errors or missing custom mutations."""

import sys
import xml.etree.ElementTree as ET
from collections import Counter

EXPECTED = {
    "com.example.lms.sqe.ExactlyOneItemMutator",
    "com.example.lms.sqe.DefaultDueDateMutator",
}


def main(path):
    mutations = ET.parse(path).getroot().findall("mutation")
    if not mutations:
        raise AssertionError("PIT produced no mutations")
    statuses = Counter(m.get("status") for m in mutations)
    invalid = {name: count for name, count in statuses.items()
               if name not in {"KILLED", "SURVIVED"}}
    if invalid:
        raise AssertionError(f"PIT execution is invalid: {invalid}")
    custom = {m.findtext("mutator"): m.get("status") for m in mutations
              if m.findtext("mutator") in EXPECTED}
    if set(custom) != EXPECTED or any(status != "KILLED" for status in custom.values()):
        raise AssertionError(f"Custom operator results missing or not killed: {custom}")
    score = 100 * statuses["KILLED"] / len(mutations)
    if score < 90:
        raise AssertionError(f"PIT score {score:.1f}% below the 90% floor")
    print(f"PIT: {len(mutations)} mutations, {statuses['KILLED']} killed, "
          f"{statuses['SURVIVED']} survived, score {score:.1f}%; custom operators killed")


if __name__ == "__main__":
    main(sys.argv[1])
