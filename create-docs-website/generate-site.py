#!/usr/bin/env python3
"""Scan a documentation directory and generate a static site manifest.

Usage:
    python3 generate-site.py <docs-directory>

Walks the given directory, discovers .md, .yaml, .yml, and other text files,
copies them into a local content/ directory preserving structure, and writes
a site-manifest.json that index.html uses to build the navigation sidebar.
"""

import json
import os
import shutil
import sys
from pathlib import Path

SUPPORTED_EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".toml", ".txt"}

def build_manifest(docs_dir: Path, root_dir: Path = None) -> dict:
    """Walk docs_dir and return a nested manifest structure."""
    if root_dir is None:
        root_dir = docs_dir

    tree = {"name": docs_dir.name, "type": "directory", "children": []}

    entries = sorted(docs_dir.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))

    for entry in entries:
        if entry.name.startswith("."):
            continue

        if entry.is_dir():
            subtree = build_manifest(entry, root_dir)
            if subtree["children"]:
                tree["children"].append(subtree)
        elif entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            rel = entry.relative_to(root_dir)
            tree["children"].append({
                "name": entry.name,
                "type": "file",
                "path": str(rel),
                "extension": entry.suffix.lower(),
            })

    return tree


def copy_content(docs_dir: Path, output_dir: Path):
    """Copy supported files from docs_dir into output_dir/content/."""
    content_dir = output_dir / "content"
    if content_dir.exists():
        shutil.rmtree(content_dir)

    for root, dirs, files in os.walk(docs_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            src = Path(root) / fname
            if src.suffix.lower() in SUPPORTED_EXTENSIONS:
                rel = src.relative_to(docs_dir)
                dst = content_dir / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <docs-directory>", file=sys.stderr)
        sys.exit(1)

    docs_dir = Path(sys.argv[1]).resolve()
    if not docs_dir.is_dir():
        print(f"Error: {docs_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(__file__).resolve().parent

    manifest = build_manifest(docs_dir)

    # Flatten the root — use the children directly since the root name
    # is just the directory name passed in.
    manifest_data = {
        "title": manifest["name"].replace("-", " ").replace("_", " ").title(),
        "pages": manifest["children"],
    }

    copy_content(docs_dir, output_dir)

    manifest_path = output_dir / "site-manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)

    page_count = sum(
        1 for _ in (output_dir / "content").rglob("*") if _.is_file()
    )
    print(f"Generated site-manifest.json with {page_count} pages")
    print(f"Content copied to {output_dir / 'content'}")
    print(f"Open index.html with a local server to view the site")


if __name__ == "__main__":
    main()
