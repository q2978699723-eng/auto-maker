"""Shared install logic: detect agent homes, unpack, copy, verify."""

from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# Agent key -> (display name, home env var, default home dir, extra hint)
TARGETS: Dict[str, dict] = {
    "dsh": {
        "label": "DeepSeek Harness",
        "env": "DSH_HOME",
        "home": "~/.dsh",
        "hint": "重启 dsh web，或新开会话即可在 skill 目录看到",
    },
    "workbuddy": {
        "label": "WorkBuddy",
        "env": "WORKBUDDY_HOME",
        "home": "~/.workbuddy",
        "hint": "在 WorkBuddy 里刷新/重开技能列表（设置 → 技能）",
    },
    "codex": {
        "label": "Codex",
        "env": None,
        "home": "~/.codex",
        "hint": "重启 codex 会话",
    },
    "claude": {
        "label": "Claude Code",
        "env": None,
        "home": "~/.claude",
        "hint": "重启 claude 会话",
    },
}

SKILL_NAME = "dsh-agent-builder"


@dataclass
class Target:
    key: str
    label: str
    home: Path
    skills_dir: Path
    exists: bool
    hint: str


def resolve_target(key: str) -> Target:
    meta = TARGETS[key]
    env = meta["env"]
    raw = os.environ.get(env) if env else None
    home = Path(os.path.expanduser(raw or meta["home"]))
    return Target(
        key=key,
        label=meta["label"],
        home=home,
        skills_dir=home / "skills",
        exists=home.is_dir(),
        hint=meta["hint"],
    )


def detect_targets() -> List[Target]:
    """Every known agent whose home directory exists on this machine."""
    return [t for t in (resolve_target(k) for k in TARGETS) if t.exists]


def pick_targets(requested: str) -> List[Target]:
    if requested == "all":
        return [resolve_target(k) for k in TARGETS]
    if requested == "auto":
        found = detect_targets()
        if not found:
            raise SystemExit(
                "没有检测到任何 agent 目录（~/.dsh、~/.workbuddy、~/.codex、~/.claude）。\n"
                "请用 --target 指定，例如 --target workbuddy，或用 --path 指定目录。"
            )
        return found
    if requested not in TARGETS:
        raise SystemExit(f"未知 target: {requested}，可选：auto / all / {' / '.join(TARGETS)}")
    return [resolve_target(requested)]


def bundled_archive() -> Path:
    return Path(__file__).resolve().parent / "data" / "auto-maker-skill.tar.gz"


def extract_skill(archive: Path, dest_root: Path) -> Path:
    """Unpack the bundled archive; return the extracted skill directory."""
    dest_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tf:
        # Python 3.12+ warns on unsafe members; validate before extracting.
        for member in tf.getmembers():
            target = (dest_root / member.name).resolve()
            if not str(target).startswith(str(dest_root.resolve())):
                raise SystemExit(f"压缩包含有非法路径: {member.name}")
        tf.extractall(dest_root)
    skill = dest_root / SKILL_NAME
    if not skill.is_dir():
        raise SystemExit(f"压缩包里没有找到 {SKILL_NAME}/ 目录")
    return skill


def read_frontmatter(skill_md: Path) -> dict:
    """Minimal YAML frontmatter reader (name/description only)."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    data: dict = {}
    key: Optional[str] = None
    for line in block.splitlines():
        if not line.strip():
            continue
        if line[0] not in " \t" and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            data[key] = value.strip()
        elif key and line.startswith((" ", "\t")):
            data[key] = (data.get(key) or "") + " " + line.strip()
    return data


def install_into(target: Target, skill_src: Path, force: bool) -> str:
    skills_dir = target.skills_dir
    skills_dir.mkdir(parents=True, exist_ok=True)
    dest = skills_dir / SKILL_NAME
    if dest.exists():
        if not force:
            return f"跳过（已存在）: {dest}   →  加 --force 覆盖"
        shutil.rmtree(dest)
    shutil.copytree(skill_src, dest)
    fm = read_frontmatter(dest / "SKILL.md")
    if fm.get("name") != SKILL_NAME:
        return f"已复制到 {dest}，但 frontmatter name={fm.get('name')!r} 与目录名不一致"
    return f"已安装: {dest}"


def uninstall_from(target: Target) -> str:
    dest = target.skills_dir / SKILL_NAME
    if not dest.exists():
        return "未安装"
    shutil.rmtree(dest)
    return f"已删除: {dest}"


def make_temp_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="auto-maker-"))
