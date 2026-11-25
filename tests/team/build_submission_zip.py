"""Package the committed repository, full Git history, and final team PDF."""

from __future__ import annotations

import subprocess
import tempfile
import zipfile
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
    tracked = subprocess.check_output(
        ["git", "ls-files", "--stage", "-z"], cwd=ROOT
    ).decode("utf-8").split("\0")
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out:
        for entry in tracked:
            if not entry:
                continue
            metadata, rel_text = entry.split("\t", 1)
            mode, _, stage = metadata.split()
            if stage != "0":
                raise RuntimeError(f"Unmerged index stages for {rel_text}")
            rel = Path(rel_text)
            if any(part in EXCLUDED_DIRS for part in rel.parts):
                continue
            path = ROOT / rel
            if path.is_file():
                info = zipfile.ZipInfo.from_file(path, Path("libris-SQE-Project") / rel)
                info.create_system = 3
                info.external_attr = int(mode, 8) << 16
                info.compress_type = out.compression
                with path.open("rb") as source, out.open(info, "w") as destination:
                    copyfileobj(source, destination)
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
    print(ARCHIVE)


if __name__ == "__main__":
    main()
