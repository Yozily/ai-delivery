# 发布步骤

面向维护本仓的人。客户不需要读这一页。

## 前提

- 产品已发版（或已发预览版），有确定的产品版本号。
- 产品仓 `delivery/<产品线>/<版本>/` 已按该版本整理并提交。

## 步骤

1. 在产品仓确认要发布的提交号。
2. 在本仓根目录生成副本：

   ```
   python3 _shared/tools/publish.py --source <产品仓路径> --product <产品线> \
       --version <版本> --product-version <产品版本> --commit <提交号>
   ```

   工具从该提交取内容（不取工作区），填写 `MANIFEST.json` 的版本、来源提交与日期；目标目录已存在时拒绝执行。

   预览版：产品尚未发版、资产已通过代理验证时，可用 `--version next --as next-preview` 发布到 `<产品线>/next-preview/`，`INDEX.md` 单列于「预览」表并注明未经完整黑盒验收。正式发版后将其状态改为 `superseded`。
3. 按 `_shared/templates/version-README.md` 写 `<产品线>/<版本>/README.md`，填好可直接复制的一句话安装提示词。
4. 更新 `INDEX.md`：加本版本行；被取代的旧版本改为 `superseded`（同时改该目录 `MANIFEST.json` 的 `status`）。
5. 运行 `python3 _shared/tools/validate.py`，必须通过。
6. 按 [self-check.md](self-check.md) 逐条确认不可机检的项。
7. 路径限定提交并推送。

## 修正与撤回

- 已发布目录的内容文件不修改。发现问题时把 `status` 改为 `yanked`，在 `INDEX.md` 顶部公告，修复后开新版本目录。
- 发现资产与产品实际行为不一致：回报产品侧修正权威源，不在本仓改内容。
