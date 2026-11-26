"""Package the committed repository, full Git history, and final team PDF."""

from __future__ import annotations

import subprocess
import tempfile
import zipfile
from copy import copy
from shutil import copyfileobj
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = "https://github.com/Artfever/libris-SQE-Project"
ARCHIVE = ROOT / "output" / "zip" / "Project_24I-3020_24I-3063_24I-3165_B.zip"
PDF = ROOT / "output" / "pdf" / "Project_24I-3020_24I-3063_24I-3165_B.pdf"
EXCLUDED_DIRS = {
    "node_modules",
    "target",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "tmp",
}


def package_history(out, commit):
    # A linked worktree's .git is a pointer to the user's main checkout.
    # Export a self-contained repository with only history reachable from HEAD.
    with tempfile.TemporaryDirectory(prefix="libris-sqe-export-") as scratch:
        root = Path(scratch)
        subprocess.run(["git", "init", "--quiet", scratch], check=True)
        subprocess.run(["git", "fetch", "--quiet", "--no-tags", str(ROOT), commit],
                       cwd=root, check=True)
        subprocess.run(["git", "switch", "--quiet", "-c", "main", "FETCH_HEAD"],
                       cwd=root, check=True)
        subprocess.run(["git", "remote", "add", "origin", REPO], cwd=root, check=True)
        subprocess.run(["git", "fsck", "--no-progress"], cwd=root, check=True,
                       stdout=subprocess.DEVNULL)
        for path in (root / ".git").rglob("*"):
            if path.is_file():
                out.write(path, Path("libris-SQE-Project") / path.relative_to(root))


def package_source(out, commit):
    # Archive committed blobs so a Windows checkout cannot change line endings
    # or executable modes in the source viewed by a Linux grader.
    with tempfile.TemporaryDirectory(prefix="libris-sqe-source-") as scratch:
        source = Path(scratch) / "source.zip"
        subprocess.run(
            ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf",
             "archive", "--format=zip", "--prefix=libris-SQE-Project/",
             f"--output={source}", commit],
            cwd=ROOT, check=True,
        )
        with zipfile.ZipFile(source) as snapshot:
            for entry in snapshot.infolist():
                if entry.is_dir() or any(part in EXCLUDED_DIRS for part in Path(entry.filename).parts):
                    continue
                archived = copy(entry)
                archived.compress_type = out.compression
                with snapshot.open(entry) as original, out.open(archived, "w") as destination:
                    copyfileobj(original, destination)


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
    with tempfile.TemporaryDirectory(prefix="assemble-", dir=ARCHIVE.parent) as scratch:
        candidate = Path(scratch) / ARCHIVE.name
        with zipfile.ZipFile(candidate, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out:
            package_source(out, commit)
            out.write(PDF, Path("libris-SQE-Project") / PDF.relative_to(ROOT))
            package_history(out, commit)
            out.writestr(
                "libris-SQE-Project/SUBMISSION_MANIFEST.txt",
                "Section B final submission\n"
                "Repository: https://github.com/Artfever/libris-SQE-Project\n"
                "Upstream: https://github.com/prathamkashyap/libris\n"
                "Exact upstream baseline: faf2bc0d28b68d4c8ff8c0ffb0fcf5bb87d42804\n"
                f"Included repository commit: {commit}\n",
            )
        candidate.replace(ARCHIVE)
    print(ARCHIVE)


if __name__ == "__main__":
    main()
