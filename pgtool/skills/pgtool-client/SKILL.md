---
name: pgtool-client
description: PgTool 客户端（桌面产测端）的只读查询与诊断。读取这台电脑上 PgTool 的数据：当前工单与环境、测试流程、部署、执行与失败原因、本机测试记录、记录同步队列，检查能否开始测试。用户问这台电脑或这条线上的 PgTool 情况时使用。与 pgtool 基础技能一起使用；不覆盖 PgTool 云后台。
metadata:
  product: PgTool
  part: client
  product-version: "v3.0.1 之后的开发构建"
  observed-at: "2026-11-02"
  access: read-only
---

# PgTool 客户端

先读 `pgtool` 技能：PgTool 的两个部分、对象区别与通用规则都在那里，本技能不重复。本技能只覆盖**客户端**，也就是装在产线电脑上的桌面产测端；数据只代表这台电脑。

最关键的三条，即使没读到 `pgtool` 也必须遵守：只发 GET 请求，不修改任何东西；结论附证据，推测要标明；云后台的问题（云端记录、多台电脑汇总、集中统计）不要用本机数据回答。

## 连接

- 客户端接口固定在本机 `http://127.0.0.1:10532`，直接使用，不要向用户询问地址或端口。
- 开始任务前先读取 `/api/shell/readiness`，`status` 为 `ready` 再继续。
- 连不上时，不要让用户提供端口，按顺序说明可能原因：
  1. 这台电脑上的 PgTool 没有启动，请用户打开 PgTool 后重试；
  2. 你没有运行在装有 PgTool 的这台电脑上（例如在云端），访问不到本机地址；
  3. 你的读取工具不允许访问本机地址，需要换一个能访问本机的工具；
  4. 管理员改过端口，此时请用户向管理员确认地址。

## 客户端规则

1. **用 ID，不用名称。** 引用项目、部署、执行、节点时用接口返回的 ID。
2. **先小后大。** 先用小接口定位，再取详情；不要一次读入整个项目或大量记录。返回被截断时，说明你看到了哪些部分。
3. **本机统计只代表这台电脑。** 不要说成全线或云端结果。

## 参考

- 日常任务做法：[references/cases.md](references/cases.md)
- 测试失败与同步失败的诊断：[references/diagnosis.md](references/diagnosis.md)
- 接口：[references/api.md](references/api.md)
- 错误与结果码：[references/errors.md](references/errors.md)
- 能力现状：[references/capabilities.md](references/capabilities.md)

## 任务路由

| 用户想做什么 | 从哪里开始 | 详见 |
|---|---|---|
| 了解这台电脑的环境、工单 | 环境类接口 | cases.md 案例 1 |
| 能不能测、启动测试 | 前提检查清单 | cases.md 案例 5 |
| 看流程内容 | 项目列表 → 工作流 → 大纲 → 节点 | cases.md 案例 2 |
| 判断流程是否已部署最新内容 | 工作流 revision；最近测试记录 → 部署 → 活跃执行 | cases.md 案例 3 |
| 修改流程 | 读取后给出修改建议 | cases.md 案例 4 |
| 测试为什么失败 | 最近测试记录；再到执行与工作台 | diagnosis.md 第 1 节 |
| 记录为什么没同步到云后台 | 同步汇总与列表 | diagnosis.md 第 2 节 |
| 云端统计、多台电脑汇总等云后台问题 | 不调用接口（仅说明，无云后台接口） | cases.md 案例 6 |
