#!/usr/bin/env python3
"""Install this local skill package. Standard library only; no network or inference."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
import uuid

NAME = "safeguard-eval"


def package_files(root: Path) -> dict[str, str]:
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Package contains a symbolic link: {path}")
        if path.is_file() and path.relative_to(root).as_posix() != "manifest.json":
            files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def verify_package(root: Path) -> dict:
    if root.is_symlink():
        raise ValueError("The package root must be a real directory, not a symbolic link.")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("name") != NAME or not isinstance(manifest.get("files"), dict):
        raise ValueError("Unrecognized package manifest.")
    for name, digest in manifest["files"].items():
        path = PurePosixPath(name)
        if (path.is_absolute() or ".." in path.parts or "\\" in name
                or path.as_posix() != name or not path.parts
                or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError(f"Invalid manifest entry: {name}")
    required = {"SKILL.md", "release.json", "scripts/install.py", "references/sources.json"}
    if not required <= manifest["files"].keys():
        raise ValueError("Required skill files are missing from the manifest.")
    actual = package_files(root)
    if actual != manifest["files"]:
        changed = sorted(set(actual) ^ set(manifest["files"]))
        changed += sorted(k for k in actual.keys() & manifest["files"].keys()
                          if actual[k] != manifest["files"][k])
        raise ValueError("Package integrity check failed: " + ", ".join(changed))
    release = json.loads((root / "release.json").read_text(encoding="utf-8"))
    if release.get("name") != NAME or release.get("version") != manifest.get("version"):
        raise ValueError("Release metadata and manifest disagree.")
    return release


def destination(target: str, scope: str, project: Path | None = None) -> Path:
    base = Path.home() if scope == "user" else (project or Path.cwd()).resolve()
    directory = ".agents" if target == "codex" else ".claude"
    return base / directory / "skills" / NAME


def install(source: Path, dest: Path, update: bool = False) -> dict:
    release = verify_package(source)
    source = source.resolve()
    dest = dest.expanduser().absolute()
    if dest.is_symlink():
        raise ValueError("Refusing to replace a symbolic-link destination. Update its source explicitly.")
    resolved = dest.resolve()
    if resolved == source or source in resolved.parents or resolved in source.parents:
        raise ValueError("Source and destination must be separate directories.")
    if dest.exists():
        if not dest.is_dir():
            raise ValueError("Destination exists and is not a directory.")
        try:
            existing = json.loads((dest / "release.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError("Destination is not a recognized Safeguard Eval installation.") from exc
        if existing.get("name") != NAME:
            raise ValueError("Refusing to replace an unrelated directory.")
        # An identical installation is a no-op; locally changed files need --update.
        try:
            verify_package(dest)
            identical = (dest / "manifest.json").read_bytes() == (source / "manifest.json").read_bytes()
        except (OSError, ValueError):
            identical = False
        if identical:
            return {"status": "unchanged", "version": release["version"], "destination": str(dest)}
        if not update:
            raise ValueError("An installation already exists. Use --update to replace it with a backup.")

    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".safeguard-eval-install-", dir=dest.parent))
    backup = None
    try:
        shutil.copytree(source, staging, dirs_exist_ok=True)
        verify_package(staging)
        if dest.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = dest.parent.parent / "skill-backups" / f"{NAME}-{stamp}-{uuid.uuid4().hex[:8]}"
            backup.parent.mkdir(parents=True, exist_ok=True)
            dest.rename(backup)
        try:
            staging.rename(dest)
        except OSError:
            if backup is not None:
                backup.rename(dest)
            raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {"status": "installed", "version": release["version"], "destination": str(dest),
            "backup": str(backup) if backup else None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=["codex", "claude-code"], required=True)
    parser.add_argument("--scope", choices=["user", "project"], default="user")
    parser.add_argument("--project", type=Path, help="Project directory for --scope project")
    parser.add_argument("--dest", type=Path, help="Override the full destination, including safeguard-eval")
    parser.add_argument("--update", action="store_true", help="Back up an existing installation before replacing it")
    args = parser.parse_args()
    if args.project and args.scope != "project":
        parser.error("--project requires --scope project")
    try:
        source = Path(__file__).resolve().parents[1]
        dest = args.dest or destination(args.target, args.scope, args.project)
        print(json.dumps(install(source, dest, args.update), indent=2))
    except (OSError, ValueError) as exc:
        print(f"Install failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
