#!/usr/bin/env python3
"""
Convert a classic-MacOS-era source tree to modern text conventions.

  * Line endings: CR (classic MacOS) and CRLF (DOS) -> LF
  * Encoding:     MacRoman text -> UTF-8 (only when the file is not already
                  valid UTF-8; pure ASCII files are unaffected)

Binary files (CELs, AIFC audio, Cinepak streams, objects, executables, ...)
are detected and left untouched.

Safe by default: it does a DRY RUN unless you pass --apply.

Usage (from the repo root, on a fresh branch):

    python convert_line_endings.py .            # dry run, shows what would change
    python convert_line_endings.py . --apply    # actually rewrite files
    python convert_line_endings.py . --apply --no-recode   # line endings only

Then review with `git diff --stat` and commit the conversion as its own
commit so later changes are easy to read.
"""

import argparse
import sys
from pathlib import Path

# Files with these extensions are treated as text without further checks.
TEXT_EXTS = {
    ".c", ".h", ".cpp", ".hpp", ".s", ".i", ".inc", ".asm",
    ".r", ".rez", ".txt", ".md", ".tcl", ".make", ".mk", ".script",
    ".cfg", ".ini", ".lst", ".map",
}

# Files with these extensions are never touched.
BINARY_EXTS = {
    ".o", ".a", ".lib", ".out", ".exe", ".app", ".rsrc", ".bin", ".dat",
    ".cel", ".aifc", ".aiff", ".aif", ".wav", ".stream", ".cine", ".bmp",
    ".img", ".iso", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".gz", ".sit",
    ".pdf", ".dll", ".so", ".dylib", ".pyc",
}

# Directories that are never descended into.
SKIP_DIRS = {".git", ".svn", ".hg", "build", "__pycache__", "node_modules"}

SAMPLE_BYTES = 8192
MAX_CONTROL_RATIO = 0.02  # more than 2% odd control bytes -> treat as binary


def looks_like_text(data: bytes) -> bool:
    """Heuristic for files with no recognised extension."""
    if not data:
        return False
    if b"\x00" in data:
        return False
    sample = data[:SAMPLE_BYTES]
    allowed = {9, 10, 12, 13}  # tab, LF, form feed, CR
    odd = sum(1 for b in sample if b < 32 and b not in allowed)
    return (odd / len(sample)) <= MAX_CONTROL_RATIO


def classify(path: Path, data: bytes) -> str:
    """Return 'text', 'binary' or 'empty'."""
    if not data:
        return "empty"
    ext = path.suffix.lower()
    if ext in BINARY_EXTS:
        return "binary"
    if b"\x00" in data[:SAMPLE_BYTES]:
        return "binary"
    if ext in TEXT_EXTS:
        return "text"
    return "text" if looks_like_text(data) else "binary"


def convert(data: bytes, recode: bool):
    """Return (new_bytes, changed_eol, recoded)."""
    new = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    changed_eol = new != data
    recoded = False

    if recode:
        try:
            new.decode("utf-8")
        except UnicodeDecodeError:
            new = new.decode("mac_roman").encode("utf-8")
            recoded = True

    return new, changed_eol, recoded


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file() and not path.is_symlink():
            yield path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", type=Path, help="repo root to process")
    ap.add_argument("--apply", action="store_true",
                    help="write changes (default is a dry run)")
    ap.add_argument("--no-recode", action="store_true",
                    help="do not convert MacRoman to UTF-8; fix line endings only")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="also list unchanged and skipped files")
    args = ap.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    n_changed = n_recoded = n_ok = n_binary = n_empty = n_err = 0

    for path in iter_files(root):
        rel = path.relative_to(root)
        try:
            data = path.read_bytes()
        except OSError as exc:
            print(f"ERROR   {rel}: {exc}", file=sys.stderr)
            n_err += 1
            continue

        kind = classify(path, data)
        if kind == "empty":
            n_empty += 1
            continue
        if kind == "binary":
            n_binary += 1
            if args.verbose:
                print(f"binary  {rel}")
            continue

        new, changed_eol, recoded = convert(data, recode=not args.no_recode)
        if new == data:
            n_ok += 1
            if args.verbose:
                print(f"ok      {rel}")
            continue

        tags = []
        if changed_eol:
            tags.append("eol")
        if recoded:
            tags.append("macroman->utf8")
            n_recoded += 1
        n_changed += 1
        print(f"{'WRITE' if args.apply else 'would '}  {rel}  [{', '.join(tags)}]")

        if args.apply:
            try:
                path.write_bytes(new)
            except OSError as exc:
                print(f"ERROR   {rel}: {exc}", file=sys.stderr)
                n_err += 1

    mode = "Applied" if args.apply else "Dry run"
    print()
    print(f"{mode}: {n_changed} file(s) to convert "
          f"({n_recoded} re-encoded), {n_ok} already fine, "
          f"{n_binary} binary skipped, {n_empty} empty, {n_err} error(s).")
    if not args.apply and n_changed:
        print("Re-run with --apply to write the changes.")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
