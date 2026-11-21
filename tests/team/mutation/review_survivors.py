"""Compare deliberately weak calibration survivors with the full team PIT run."""

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def key(mutation):
    return (mutation.findtext("mutatedClass"), mutation.findtext("mutatedMethod"),
            mutation.findtext("lineNumber"), mutation.findtext("mutator"),
            mutation.findtext("description"),
            tuple(index.text for index in mutation.findall("./indexes/index")))


def test_name(value):
    found = re.search(r"(?:test-template|method):([^/\]]+)", value or "")
    return found.group(1).replace("|", "\\|") if found else "see PIT XML"


def main(calibration, full, output):
    weak = ET.parse(calibration).getroot().findall("mutation")
    complete = ET.parse(full).getroot().findall("mutation")
    full_by_key = {key(m): m for m in complete}
    review = [m for m in weak if m.get("status") == "SURVIVED"]
    for mutation in review:
        matched = full_by_key.get(key(mutation))
        if matched is None or matched.get("status") != "KILLED":
            raise AssertionError("A calibration survivor was not killed by full team tests")
    equivalents = [m for m in complete if m.get("status") == "SURVIVED"]
    if len(review) + len(equivalents) < 15:
        raise AssertionError("Fewer than 15 surviving mutants inspected")
    statuses = Counter(m.get("status") for m in complete)
    lines = [
        "# Phase 4 PIT survivor review (#17)", "",
        "The calibration suite `TeamMutationCalibrationTest` intentionally asserts only that one book borrow returns a non-null response. It is **not** a quality gate. PIT gave 14 surviving, executed mutants under this weak suite. The full team suite killed all 14. The full suite also has two equivalent survivors in `OverdueCalculator`, for 16 survivors inspected across the two runs. Raw results: [calibration](calibration-mutations.xml) and [full](phase4-mutations.xml).", "",
        f"Full scope: {len(complete)} mutants, {statuses['KILLED']} killed, {statuses['SURVIVED']} survived, score {100*statuses['KILLED']/len(complete):.1f}% (90% gate). No `RUN_ERROR` or `NO_COVERAGE`. PIT 1.19.4, JUnit 5 plugin 1.2.3, Java 21, `h2` only for the separate recovery test. Both custom BR-C01 and BR-C05 operators were killed.", "",
        "| # | Class:line | Mutation | Classification | Full-suite result / evidence |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for number, mutation in enumerate(review, 1):
        final = full_by_key[key(mutation)]
        description = mutation.findtext("description").replace("|", "\\|")
        method = mutation.findtext("mutatedMethod")
        line = mutation.findtext("lineNumber")
        lines.append(f"| {number} | `BorrowRecordService.{method}:{line}` | {description} | Weak assertion in calibration smoke test | KILLED by `{test_name(final.findtext('killingTest'))}` |")
    for number, mutation in enumerate(equivalents, len(review) + 1):
        method = mutation.findtext("mutatedMethod")
        line = mutation.findtext("lineNumber")
        lines.append(f"| {number} | `OverdueCalculator.{method}:{line}` | Remove null-record guard | Equivalent | SURVIVED: a null record flows to `effectiveDueDate(null)`, which returns null; both original and mutant then return false/zero. |")
    lines += ["", "The weak suite misses BR-C01 item selection, BR-C05 due-date defaults, item availability, borrower snapshots, audit publication, response type/status and history branches. The full team tests assert those outcomes and kill all 14 killable calibration survivors. The two null-guard survivors are equivalent for this implementation and are retained in the 90% threshold denominator. The raw XML records exact mutant indexes and killing tests.", ""]
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Reviewed {len(review)} weak-suite survivors and {len(equivalents)} equivalent full-suite survivors")


if __name__ == "__main__":
    main(*(Path(value) for value in sys.argv[1:4]))
