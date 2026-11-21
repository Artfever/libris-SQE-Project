"""Package the committed repository, full Git history, and final team PDF."""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "output" / "zip" / "Project_24I-3020_24I-3063_24I-3165_B.zip"
PDF = ROOT / "output" / "pdf" / "Project_24I-3020_24I-3063_24I-3165_B.pdf"
EXCLUDED_DIRS = {
    "node_modules",
    "target",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
}


def main() -> None:
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True
    )
    if status.strip():
        raise RuntimeError("Commit all repository changes before building the submission ZIP")
    if not PDF.is_file():
        raise FileNotFoundError(PDF)

    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out:
        for path in ROOT.rglob("*"):
            rel = path.relative_to(ROOT)
            if any(part in EXCLUDED_DIRS for part in rel.parts):
                continue
            if rel.parts[0] == "output":
                if rel != Path("output/pdf/Project_24I-3020_24I-3063_24I-3165_B.pdf"):
                    continue
            if path.is_file() and (rel.parts[0] == ".git" or rel.parts[0] != "output"):
                out.write(path, Path("libris-SQE-Project") / rel)
        out.writestr(
            "libris-SQE-Project/SUBMISSION_MANIFEST.txt",
            "Section B final submission\n"
            "Repository: https://github.com/Artfever/libris-SQE-Project\n"
            "Upstream: https://github.com/prathamkashyap/libris\n"
            "Exact upstream baseline: faf2bc0d28b68d4c8ff8c0ffb0fcf5bb87d42804\n"
            f"Included repository commit: {commit}\n",
        )
    print(ARCHIVE)


if __name__ == "__main__":
    main()
