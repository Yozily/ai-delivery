#!/usr/bin/env python3
"""从产品仓生成发布仓副本：《对外AI交付资产规范》§7 第 4 步。

内容取自产品仓某个确定提交（git archive），不取工作区，保证副本可由 sourceCommit 复现。
目标版本目录已存在时拒绝执行：旧版本不覆盖。

用法（在发布仓根目录）：
  python3 _shared/tools/publish.py \
      --source <产品仓路径> --product pgtool --version 3.1.0 \
      --product-version 3.1.0 [--commit <提交号，默认 HEAD>] [--released-at YYYY-MM-DD]

完成后还需：按 _shared/templates/version-README.md 写版本 README，更新 INDEX.md，
再运行 _shared/tools/validate.py。只用 Python 标准库与 git。
"""
import argparse
import datetime
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(src, *args):
    return subprocess.run(["git", "-C", str(src), *args], check=True,
                          capture_output=True).stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="产品仓路径")
    ap.add_argument("--product", required=True)
    ap.add_argument("--version", required=True, help="delivery/<product>/ 下的版本目录名")
    ap.add_argument("--product-version", required=True, help="对应的产品运行版本")
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--released-at", default=datetime.date.today().isoformat())
    a = ap.parse_args()

    src = Path(a.source).resolve()
    commit = git(src, "rev-parse", "--verify", f"{a.commit}^{{commit}}").decode().strip()
    prefix = f"delivery/{a.product}/{a.version}"
    if not git(src, "ls-tree", "-d", commit, prefix).strip():
        sys.exit(f"产品仓提交 {commit[:9]} 中不存在 {prefix}/")
    dirty = git(src, "status", "--porcelain", "--", prefix).decode().strip()
    if dirty:
        print(f"提示：产品仓工作区中 {prefix}/ 有未提交改动，本次只发布提交 {commit[:9]} 中的内容。")

    target = ROOT / a.product / a.version
    if target.exists():
        sys.exit(f"目标已存在：{target.relative_to(ROOT)}。旧版本不覆盖；如需修正请开新版本目录。")

    data = git(src, "archive", "--format=tar", commit, prefix)
    target.mkdir(parents=True)
    count = 0
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            rel = Path(m.name).relative_to(prefix)
            out = target / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(tar.extractfile(m).read())
            count += 1

    mf = target / "MANIFEST.json"
    manifest = json.loads(mf.read_text(encoding="utf-8")) if mf.is_file() else {}
    manifest.update({
        "product": a.product,
        "version": a.version,
        "status": "released",
        "productVersion": a.product_version,
        "sourceRepo": src.name,
        "sourceCommit": commit,
        "releasedAt": a.released_at,
        "generatedBy": "_shared/tools/publish.py",
    })
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"已生成 {target.relative_to(ROOT)}/：{count} 个文件，来源 {src.name}@{commit[:9]}")
    print("下一步：写版本 README.md、更新 INDEX.md，然后运行 python3 _shared/tools/validate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
