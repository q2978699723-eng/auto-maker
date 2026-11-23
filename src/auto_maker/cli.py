"""Command line entry point: auto-maker install | list | uninstall | doctor."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from . import __version__
from .installer import (
    SKILL_NAME,
    TARGETS,
    bundled_archive,
    detect_targets,
    extract_skill,
    install_into,
    make_temp_dir,
    pick_targets,
    read_frontmatter,
    resolve_target,
    uninstall_from,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="auto-maker",
        description="把 dsh-agent-builder skill 安装到本机的 agent（DeepSeek Harness / WorkBuddy / Codex / Claude）",
    )
    p.add_argument("--version", action="version", version=f"auto-maker {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    def add_target_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--target",
            default="auto",
            help="auto（默认，装到所有已检测到的 agent）/ all / " + " / ".join(TARGETS),
        )
        sp.add_argument("--path", help="直接指定 skills 目录（覆盖 --target）")

    ins = sub.add_parser("install", help="安装 skill")
    add_target_args(ins)
    ins.add_argument("--force", action="store_true", help="已存在时覆盖")
    ins.add_argument("--dry-run", action="store_true", help="只显示会做什么")

    rm = sub.add_parser("uninstall", help="卸载 skill")
    add_target_args(rm)

    sub.add_parser("list", help="列出本机检测到的 agent 与安装状态")

    doc = sub.add_parser("doctor", help="校验打包内容与已安装副本")
    doc.add_argument("--target", default="auto")
    return p


def cmd_list() -> int:
    found = detect_targets()
    print(f"打包版本: {__version__}    skill: {SKILL_NAME}\n")
    if not found:
        print("未检测到任何 agent 目录。")
        print("可用 --target 强制指定：" + " / ".join(TARGETS))
        return 1
    for t in found:
        state = "已安装" if (t.skills_dir / SKILL_NAME).is_dir() else "未安装"
        print(f"  {'✓' if state == '已安装' else '·'} {t.label:<20} {t.skills_dir}   [{state}]")
    missing = [k for k in TARGETS if not resolve_target(k).exists]
    if missing:
        print("\n未检测到: " + ", ".join(TARGETS[k]["label"] for k in missing))
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    archive = bundled_archive()
    if not archive.is_file():
        print(f"错误：打包内缺少 {archive}", file=sys.stderr)
        return 2

    if args.path:
        dest = Path(args.path).expanduser()
        targets = []
        if args.dry_run:
            print(f"[dry-run] 将安装到 {dest / SKILL_NAME}")
            return 0
        dest.mkdir(parents=True, exist_ok=True)
        tmp = make_temp_dir()
        src = extract_skill(archive, tmp)
        final = dest / SKILL_NAME
        if final.exists() and not args.force:
            print(f"跳过（已存在）: {final}   →  加 --force 覆盖")
        else:
            if final.exists():
                shutil.rmtree(final)
            shutil.copytree(src, final)
            print(f"已安装: {final}")
        shutil.rmtree(tmp, ignore_errors=True)
        return 0

    targets = pick_targets(args.target)
    if not targets:
        print("没有可安装的目标。", file=sys.stderr)
        return 1

    if args.dry_run:
        for t in targets:
            print(f"[dry-run] {t.label}: {t.skills_dir / SKILL_NAME}")
        return 0

    tmp = make_temp_dir()
    try:
        src = extract_skill(archive, tmp)
        fm = read_frontmatter(src / "SKILL.md")
        print(f"打包版本 {__version__} | 技能 {fm.get('name')} | 目标 {len(targets)} 个\n")
        rc = 0
        for t in targets:
            result = install_into(t, src, args.force)
            print(f"  {t.label:<20} {result}")
            if result.startswith("已安装"):
                print(f"  {'':<20} ↳ {t.hint}")
        return rc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_uninstall(args: argparse.Namespace) -> int:
    if args.path:
        dest = Path(args.path).expanduser() / SKILL_NAME
        if dest.exists():
            shutil.rmtree(dest)
            print(f"已删除: {dest}")
        else:
            print("未安装")
        return 0
    for t in pick_targets(args.target):
        print(f"  {t.label:<20} {uninstall_from(t)}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    archive = bundled_archive()
    if not archive.is_file():
        print("✗ 打包内缺少 skill 压缩包")
        return 2
    tmp = make_temp_dir()
    try:
        src = extract_skill(archive, tmp)
        fm = read_frontmatter(src / "SKILL.md")
        ok = fm.get("name") == SKILL_NAME and bool(fm.get("description"))
        print(f"{'✓' if ok else '✗'} 压缩包内 SKILL.md frontmatter（name / description）")
        refs = sorted(p.name for p in (src / "references").glob("*.md")) if (src / "references").is_dir() else []
        print(f"✓ references: {', '.join(refs) if refs else '（无）'}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for t in pick_targets(args.target):
        dest = t.skills_dir / SKILL_NAME
        if dest.is_dir():
            fm = read_frontmatter(dest / "SKILL.md")
            print(f"✓ {t.label}: {dest} (name={fm.get('name')})")
        else:
            print(f"· {t.label}: 未安装")
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "install":
        return cmd_install(args)
    if args.command == "uninstall":
        return cmd_uninstall(args)
    if args.command == "list":
        return cmd_list()
    if args.command == "doctor":
        return cmd_doctor(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
