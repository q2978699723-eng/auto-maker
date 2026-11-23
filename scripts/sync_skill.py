#!/usr/bin/env python3
"""Rebuild the packaged skill archive from ../skills/dsh-agent-builder."""
from __future__ import annotations

import hashlib
import io
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "skills" / "dsh-agent-builder"
OUT = ROOT / "src" / "auto_maker" / "data" / "auto-maker-skill.tar.gz"
SKIP = {".DS_Store"}


def main() -> None:
    if not (SRC / "SKILL.md").is_file():
        raise SystemExit(f"missing skill source: {SRC}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in SRC.rglob("*") if p.is_file() and p.name not in SKIP)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for path in files:
            arc = Path("dsh-agent-builder") / path.relative_to(SRC)
            info = tf.gettarinfo(str(path), arcname=str(arc))
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 0
            with path.open("rb") as fh:
                tf.addfile(info, fh)
    data = buf.getvalue()
    OUT.write_bytes(data)
    print(f"wrote {OUT.relative_to(ROOT)}  files={len(files)}  sha256={hashlib.sha256(data).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
