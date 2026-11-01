#!/usr/bin/env python3
"""发布仓校验：按《对外AI交付资产规范》§4、§6 检查每个 <产品线>/<版本>/ 目录。

用法（在发布仓根目录）：
  python3 _shared/tools/validate.py            # 校验全部版本目录
  python3 _shared/tools/validate.py pgtool/3.1.0   # 只校验指定目录
退出码 0 表示通过，1 表示有错误。只用 Python 标准库。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_TOP = {"_shared", ".git", ".github"}
REQUIRED = ["product", "version", "status", "productVersion", "sourceRepo",
            "sourceCommit", "releasedAt", "compat", "assets"]
STATUSES = {"released", "superseded", "yanked"}
ASSET_KINDS = ["skills", "mcp", "prompts", "docs"]
TEXT_SUFFIXES = {".md", ".json", ".txt", ".yaml", ".yml"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BANNED = [
    (re.compile(r"\.project/"), "引用内部设计目录 .project/"),
    (re.compile(r"\.agents/"), "引用内部开发目录 .agents/"),
    (re.compile(r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "内网地址 10.x"),
    (re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"), "内网地址 192.168.x"),
    (re.compile(r"\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b"), "内网地址 172.16-31.x"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "私钥"),
    (re.compile(r"://[^/\s:@]+:[^/\s@]+@"), "URL 内嵌凭据"),
    (re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}"), "疑似凭据赋值"),
    (re.compile(r"/Users/|[A-Za-z]:\\\\"), "本机文件路径"),
]


class Report:
    def __init__(self):
        self.errors = []

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")


def frontmatter(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    fields = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip().strip('"')
    return fields


def check_skill(skill_dir, rep, where):
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        rep.err(where, f"{skill_dir.name}: 缺少 SKILL.md")
        return
    fm = frontmatter(md.read_text(encoding="utf-8"))
    if fm is None:
        rep.err(where, f"{md.relative_to(ROOT)}: 缺少 YAML frontmatter")
        return
    name = fm.get("name", "")
    if name != skill_dir.name:
        rep.err(where, f"{md.relative_to(ROOT)}: name「{name}」与目录名不一致")
    if not (1 <= len(name) <= 64 and NAME_RE.match(name)):
        rep.err(where, f"{md.relative_to(ROOT)}: name 不符合规范（小写字母、数字、单个连字符，最长 64）")
    desc = fm.get("description", "")
    if not (1 <= len(desc) <= 1024):
        rep.err(where, f"{md.relative_to(ROOT)}: description 长度应为 1–1024")


def check_links(vdir, rep, where):
    for f in vdir.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            if re.match(r"^[a-z]+://", target) or target.startswith("#") or target.startswith("mailto:"):
                continue
            path = target.split("#", 1)[0]
            if not path:
                continue
            resolved = (f.parent / path).resolve()
            try:
                resolved.relative_to(vdir.resolve())
            except ValueError:
                rep.err(where, f"{f.relative_to(ROOT)}: 链接越出版本目录：{target}")
                continue
            if not resolved.exists():
                rep.err(where, f"{f.relative_to(ROOT)}: 链接无法解析：{target}")


def check_banned(vdir, rep, where):
    for f in vdir.rglob("*"):
        if not f.is_file() or f.suffix not in TEXT_SUFFIXES:
            continue
        for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for pat, label in BANNED:
                if pat.search(line):
                    rep.err(where, f"{f.relative_to(ROOT)}:{lineno}: {label}")


def check_assets(vdir, manifest, rep, where):
    assets = manifest.get("assets") or {}
    listed = set()
    for kind in ASSET_KINDS:
        for item in assets.get(kind, []) or []:
            for key in ("name", "path", "purpose"):
                if not item.get(key):
                    rep.err(where, f"assets.{kind} 条目缺少 {key}")
            p = item.get("path", "")
            listed.add(p)
            if p and not (vdir / p).is_file():
                rep.err(where, f"assets.{kind}: 路径不存在：{p}")
    actual = set()
    if (vdir / "skills").is_dir():
        for d in sorted((vdir / "skills").iterdir()):
            if d.is_dir():
                actual.add(f"skills/{d.name}/SKILL.md")
                check_skill(d, rep, where)
    if (vdir / "mcp").is_dir():
        for d in sorted((vdir / "mcp").iterdir()):
            if d.is_dir():
                actual.add(f"mcp/{d.name}/contract.md")
    for kind in ("prompts", "docs"):
        if (vdir / kind).is_dir():
            for f in sorted((vdir / kind).glob("*.md")):
                actual.add(f"{kind}/{f.name}")
    for missing in sorted(actual - listed):
        rep.err(where, f"目录中有资产未登记到 MANIFEST.assets：{missing}")
    for kind in ASSET_KINDS:
        d = vdir / kind
        if d.is_dir() and not any(d.iterdir()):
            rep.err(where, f"空目录 {kind}/（未验证的形态不应留空壳）")


def check_readme(vdir, rep, where):
    readme = vdir / "README.md"
    if not readme.is_file():
        rep.err(where, "缺少版本 README.md")
        return
    text = readme.read_text(encoding="utf-8")
    if "<!--" in text:
        rep.err(where, "README.md 仍含模板注释")
    leftovers = re.findall(r"<[^<>\s/][^<>]*[\u4e00-\u9fff][^<>]*>", text)
    if leftovers:
        rep.err(where, f"README.md 仍有未填写的占位：{', '.join(sorted(set(leftovers))[:5])}")


def check_version(vdir, rep, index_text):
    where = str(vdir.relative_to(ROOT))
    mf = vdir / "MANIFEST.json"
    if not mf.is_file():
        rep.err(where, "缺少 MANIFEST.json")
        return
    try:
        manifest = json.loads(mf.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        rep.err(where, f"MANIFEST.json 解析失败：{e}")
        return
    for key in REQUIRED:
        if manifest.get(key) in (None, "", []):
            rep.err(where, f"MANIFEST.{key} 缺失或为空")
    if manifest.get("product") != vdir.parent.name:
        rep.err(where, "MANIFEST.product 与产品线目录名不一致")
    if manifest.get("version") != vdir.name:
        rep.err(where, "MANIFEST.version 与版本目录名不一致")
    if manifest.get("status") not in STATUSES:
        rep.err(where, f"MANIFEST.status 应为 {sorted(STATUSES)}")
    if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("sourceCommit", ""))):
        rep.err(where, "MANIFEST.sourceCommit 应为 40 位提交号")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(manifest.get("releasedAt", ""))):
        rep.err(where, "MANIFEST.releasedAt 应为 YYYY-MM-DD")
    if "_comment" in manifest:
        rep.err(where, "MANIFEST.json 仍含模板 _comment 字段")
    check_assets(vdir, manifest, rep, where)
    check_readme(vdir, rep, where)
    check_links(vdir, rep, where)
    check_banned(vdir, rep, where)
    row = re.search(r"^\|\s*" + re.escape(vdir.parent.name) + r"\s*\|\s*" + re.escape(vdir.name) + r"\s*\|\s*([a-z]+)\s*\|", index_text, re.M)
    if not row:
        rep.err(where, "INDEX.md 中没有本版本的行")
    elif row.group(1) != manifest.get("status"):
        rep.err(where, f"INDEX.md 状态「{row.group(1)}」与 MANIFEST.status 不一致")


def version_dirs(args):
    if args:
        return [(ROOT / a).resolve() for a in args]
    dirs = []
    for prod in sorted(ROOT.iterdir()):
        if prod.is_dir() and prod.name not in SKIP_TOP and not prod.name.startswith("."):
            dirs.extend(sorted(d for d in prod.iterdir() if d.is_dir()))
    return dirs


def main():
    rep = Report()
    index_path = ROOT / "INDEX.md"
    index_text = index_path.read_text(encoding="utf-8") if index_path.is_file() else ""
    dirs = version_dirs(sys.argv[1:])
    for vdir in dirs:
        if not vdir.is_dir():
            rep.err(str(vdir), "目录不存在")
            continue
        check_version(vdir, rep, index_text)
    check_links_root(rep)
    if rep.errors:
        print(f"校验未通过：{len(rep.errors)} 项")
        for e in rep.errors:
            print(f"  - {e}")
        return 1
    print(f"校验通过：{len(dirs)} 个版本目录")
    return 0


def check_links_root(rep):
    for name in ("README.md", "INDEX.md", "INSTALL.md"):
        f = ROOT / name
        if not f.is_file():
            continue
        for target in LINK_RE.findall(f.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+://", target) or target.startswith("#"):
                continue
            path = target.split("#", 1)[0]
            if path and not (ROOT / path).exists():
                rep.err(name, f"链接无法解析：{target}")


if __name__ == "__main__":
    sys.exit(main())
