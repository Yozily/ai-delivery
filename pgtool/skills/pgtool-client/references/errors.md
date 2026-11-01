# 错误与结果码

本页列出客户端接口的错误形态，以及截至观测日期出现过的结果码与错误码。遇到未列出的码，按其消息字面理解，并在回答中注明「未收录的码」。

## 1. 错误形态

| 形态 | 特征字段 | 处理 |
|---|---|---|
| 通用错误 | `type`、`title`、`status`、`traceId`，参数错误时带 `errors` | 400：按 `errors` 修正参数；404 且没有 `outcomeCode`：对象不存在或路径不对；向用户报告时带上 `traceId` |
| 信封 | `code`、`message`、`data` | `code` 为 0 表示成功 |
| 编辑诊断 | `message`、`diagnostics[{severity, code, path, message}]` | 按 `code` 与 `path` 定位 |
| 结果码 | `stage`、`outcomeCode` | 见第 2 节。**以 `outcomeCode` 为准，不看 HTTP 状态码**：正常的「没有」也会返回 404 或 409 |
| 已下线 | `code: 410` 与替代说明 | 接口不可用，不要重试 |

## 2. 结果码（outcomeCode）

返回体带 `outcomeCode` 时，按下表理解，不要因为 HTTP 状态码是 404 就以为路径写错而改参数重试。

| 结果码 | HTTP | 含义 | 处理 |
|---|---|---|---|
| `workflow-v2.production-execution-discovery.current` | 200 | 找到该部署的活跃执行 | 正常 |
| `workflow-v2.production-execution-discovery.not-found` | 404 | 该部署当前没有活跃执行 | 正常，不是故障 |
| `workflow-v2.production-execution-discovery.recent` | 200 | 找到该部署的最近执行 | 正常 |
| `workflow-v2.production-execution-discovery.recent-not-found` | 404 | 该部署没有最近执行 | 正常，不是故障 |
| `workflow.runtime.status.current` | 200 | 执行状态读取成功 | 正常 |
| `production-testing.workflow-debug.snapshot-current` | 200 | 调试快照为当前状态 | 正常 |
| `workflow-v2.production-configuration.session-binding-not-found` | 409 | 该执行的生产配置会话绑定不存在，工作台与调试快照读不到 | 改走测试记录或死信事件；作为线索报告 |
| `workflow.runtime.access.ownership_scope_denied` | 未记录 | 当前访问身份无权读取该执行 | 不要重试；作为线索报告，需要时请管理员协助 |

## 3. 执行失败码

工作台 `executionFailures`、调试快照 `failureCode` 与死信事件中可能出现。测试流程中的断言也可以自定义失败码，其含义以随附的消息为准。

| 失败码 | 含义 | 处理 |
|---|---|---|
| `production-testing.test-item-result.test-run-not-found` | 无法记录测试结果：当前执行没有关联到测试记录 | 转述消息中的建议（停止本次测试，检查工位会话的创建与绑定）；停止测试需用户在界面操作 |
| `client-subapp.ownership.unknown:no-owner`（死信原因） | 节点事件无法归属到工位会话，未能落库 | 作为线索报告：工位会话的归属缺失 |

## 4. 同步错误码（lastErrorCode）

| 错误码 | 含义 | 找谁 | 重试 |
|---|---|---|---|
| `remote_unavailable` | 云后台不可达（连接被拒、网关 502 等，看 `lastErrorReason`） | 运维 | 修好后手动重试 |
| `identity_provider_unavailable` | 身份服务发不出机器令牌 | 身份服务管理员 | 修好后手动重试 |
| `identity_provider_rejected` | 身份服务拒绝签发 | 身份服务管理员 | 修好后手动重试 |
| `identity_provider_rate_limited` | 身份服务限流，本身是临时问题 | 无需找人 | 稍后手动重试 |
| `invalid_client` | 机器凭据已失效 | 平台管理员 | 修好后手动重试 |
| `machine_credential_unavailable` | 机器凭据缺失 | 平台管理员 | 修好后手动重试 |
| `forbidden` | 凭据没有上传权限 | 平台管理员 | 修好后手动重试 |

重试由用户在界面操作，你不发起重试。
