# 返回与错误

本页是客户端接口的返回形态、错误形态与通用结果码。各业务域特有的错误码在对应参考文件中：执行失败码见 [run.md](run.md)，同步错误码见 [sync.md](sync.md)。遇到未列出的码，按其消息字面理解，并在回答中注明「未收录的码」。

## 1. 成功返回形态

| 形态 | 结构 | 例子 |
|---|---|---|
| 信封 | `{code, message, length, data: {value, total}}`；`code` 为 0 表示成功；`length` 是本次返回条数，`total` 是总数（部分接口没有 `total`，如本机统计） | 生产上下文、系统状态、记录检索、本机统计 |
| 分页对象 | `{items, total, page, pageSize}` | 同步列表 |
| 带版本的结果 | `{revision, value}`；`revision` 在顶层，形如 `<哈希>:<时间>`；内容在 `value` | 工作流列表、大纲 |
| 结果码 | `{stage, outcomeCode, …}` | 活跃执行、最近执行、工作台与调试快照的失败结果 |
| 裸数组或裸对象 | 无外层包装 | 项目列表、部署列表、就绪、身份状态 |

体量：标「大」的接口可能超过你的工具单次读取上限，只返回一部分时，结论要说明这一点。

空列表或空字段不一定表示「没有」，也可能是未配置；说明时区分「接口返回为空」和「对象不存在」。

## 2. 错误形态

| 形态 | 特征字段 | 处理 |
|---|---|---|
| 通用错误 | `type`、`title`、`status`、`traceId`，参数错误时带 `errors` | 400：按 `errors` 修正参数；404 且没有 `outcomeCode`：对象不存在或路径不对；向用户报告时带上 `traceId` |
| 编辑诊断 | `message`、`diagnostics[{severity, code, path, message}]` | 按 `code` 与 `path` 定位 |
| 结果码 | `stage`、`outcomeCode` | **以 `outcomeCode` 为准，不看 HTTP 状态码**；见第 3 节 |
| 已下线 | `code: 410` 与替代说明 | 接口不可用，不要重试 |

## 3. 结果码（outcomeCode）

返回体带 `outcomeCode` 时按下表理解。不要因为 HTTP 状态码是 404 就以为路径写错而改参数重试。

| 结果码 | HTTP | 含义 | 处理 |
|---|---|---|---|
| `workflow-v2.production-execution-discovery.current` | 200 | 找到该部署的活跃执行 | 正常 |
| `workflow-v2.production-execution-discovery.not-found` | 404 | 该部署当前没有活跃执行 | 正常，不是故障 |
| `workflow-v2.production-execution-discovery.recent` | 200 | 找到该部署的最近执行 | 正常 |
| `workflow-v2.production-execution-discovery.recent-not-found` | 404 | 该部署没有最近执行 | 正常，不是故障 |
| `workflow.runtime.status.current` | 200 | 执行状态读取成功 | 正常 |
| `production-testing.workflow-debug.snapshot-current` | 200 | 调试快照为当前状态 | 正常 |
| `workflow-v2.production-configuration.session-binding-not-found` | 409 | 该执行的生产配置会话绑定不存在，工作台与调试快照读不到 | 换诊断路径（见 [run-diagnose.md](run-diagnose.md)）；作为线索报告 |
| `workflow.runtime.access.ownership_scope_denied` | 未记录 | 当前访问身份无权读取该执行 | 不要重试；作为线索报告，需要时请管理员协助 |

## 4. 时间

- 带 `+00:00` 或 `Utc` 后缀的是 UTC 时间。
- 同步列表的 `recordCreatedAt`、测试记录的 `createTime` 没有时区标记，是这台电脑的本地时间。
- 与用户说时间时注明时区，比较前先统一。
