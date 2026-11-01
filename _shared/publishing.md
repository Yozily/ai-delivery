# 发布步骤

面向维护本仓的人。客户不需要读这一页。

## 目录约定

- `<产品线>/`：当前版本，滚动更新。安装地址固定，客户更新后重新安装即可。
- `<产品线>/releases/<X.Y.Z>/`：产品正式发版时的快照，生成后不再修改，供使用旧版本产品的客户安装。
- 版本历史由 Git 记录；`releases/` 只为方便按产品版本查找。

## 更新当前版本

1. 产品仓 `delivery/<产品线>/` 的改动已提交，记下提交号。
2. 在本仓根目录：

   ```
   python3 _shared/tools/publish.py --source <产品仓路径> --product <产品线> \
       --product-version "<内容对应的产品版本>" --commit <提交号>
   ```

   工具从该提交取内容（不取工作区），替换 `<产品线>/` 下的内容文件，保留 `README.md` 与 `releases/`，并填写 `MANIFEST.json` 的来源提交与日期。
3. 能力或适用范围有变化时，更新 `<产品线>/README.md` 与 `INDEX.md`。
4. 运行 `python3 _shared/tools/validate.py`，必须通过。
5. 路径限定提交并推送。

## 产品发版时存快照

1. 用产品发版提交（或标签）执行上面的命令，加 `--release <X.Y.Z>`，生成 `<产品线>/releases/<X.Y.Z>/`；已存在时拒绝执行。
2. 为快照写 `README.md`（可参照 `_shared/templates/version-README.md`）。
3. `INDEX.md` 加快照行；之前的快照改为 `superseded`（同时改其 `MANIFEST.json` 的 `status`）。
4. 同时更新当前版本，`MANIFEST.json` 的 `status` 在完成黑盒验收后由 `preview` 改为 `released`。
5. 校验、提交、推送。

## 修正与撤回

- 当前版本有问题：修正产品仓后重新发布即可。
- 快照有问题：快照内容不修改。把 `status` 改为 `yanked`，在 `INDEX.md` 顶部公告，并说明替代版本。
- 发现资产与产品实际行为不一致：回报产品侧修正权威源，不在本仓改内容。
