#!/usr/bin/env python3
"""从产品仓生成发布仓内容：《对外AI交付资产规范》§7。

每条产品线在发布仓有两类目录：
  <产品线>/                    当前版本，滚动更新（保留其中的 README.md 与 releases/）
  <产品线>/releases/<X.Y.Z>/   产品发版时的快照，生成后不再修改

内容一律取自产品仓某个确定提交的 delivery/<产品线>/（git archive），不取工作区。

用法（在发布仓根目录）：
  更新当前版本：
    python3 _shared/tools/publish.py --source <产品仓路径> --product pgtool \\
        --product-version "<产品版本>" [--commit <提交号，默认 HEAD>]
  产品发版时存快照：
    python3 _shared/tools/publish.py --source <产品仓路径> --product pgtool \\
        --product-version 3.1.0 --release 3.1.0 --commit <发版提交或标签>

完成后检查 README.md、INDEX.md，再运行 _shared/tools/validate.py。只用 Python 标准库与 git。
"""
import argparse
import datetime
import io
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEEP_IN_CURRENT = {"README.md", "releases"}


def git(src, *args):
    return subprocess.run(["git", "-C", str(src), *args], check=True,
                          capture_output=True).stdout


def extract(data, prefix, target):
    count = 0
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            rel = Path(m.name).relative_to(prefix)
            if rel.parts and rel.parts[0] in KEEP_IN_CURRENT:
                continue
            out = target / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(tar.extractfile(m).read())
            count += 1
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="产品仓路径")
    ap.add_argument("--product", required=True)
    ap.add_argument("--product-version", required=True, help="内容对应的产品版本")
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--release", help="存为 releases/<版本> 快照；不给则更新当前版本")
    ap.add_argument("--released-at", default=datetime.date.today().isoformat())
    a = ap.parse_args()

    src = Path(a.source).resolve()
    commit = git(src, "rev-parse", "--verify", f"{a.commit}^{{commit}}").decode().strip()
    prefix = f"delivery/{a.product}"
    if not git(src, "ls-tree", "-d", commit, prefix).strip():
        sys.exit(f"产品仓提交 {commit[:9]} 中不存在 {prefix}/")
    if git(src, "status", "--porcelain", "--", prefix).decode().strip():
        print(f"提示：产品仓工作区中 {prefix}/ 有未提交改动，本次只发布提交 {commit[:9]} 中的内容。")

    product_dir = ROOT / a.product
    if a.release:
        target = product_dir / "releases" / a.release
        if target.exists():
            sys.exit(f"快照已存在：{target.relative_to(ROOT)}。快照不覆盖。")
        target.mkdir(parents=True)
    else:
        target = product_dir
        target.mkdir(exist_ok=True)
        for child in target.iterdir():
            if child.name in KEEP_IN_CURRENT:
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()

    count = extract(git(src, "archive", "--format=tar", commit, prefix), prefix, target)

    mf = target / "MANIFEST.json"
    manifest = json.loads(mf.read_text(encoding="utf-8")) if mf.is_file() else {}
    manifest.update({
        "product": a.product,
        "version": a.release or "current",
        "productVersion": a.product_version,
        "sourceRepo": src.name,
        "sourceCommit": commit,
        "releasedAt": a.released_at,
        "generatedBy": "_shared/tools/publish.py",
    })
    if a.release:
        manifest["status"] = "released"
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    where = target.relative_to(ROOT)
    print(f"已生成 {where}/：{count} 个文件，来源 {src.name}@{commit[:9]}:{prefix}/")
    print("下一步：检查 README.md 与 INDEX.md，然后运行 python3 _shared/tools/validate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
