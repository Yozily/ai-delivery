# 测试为什么失败

只读诊断。按「现象、影响范围、证据、可能原因、建议下一步」回答。依次尝试以下路径，哪条走得通用哪条。

## 路径 A：从测试记录出发（最常用）

1. 按 `pgtool-record` 取最近一条记录（`Page=1&PageSize=1`）；需要特定工单时加 `OrderNumber`。
2. 按 [pgtool-record-read.md](../../pgtool-record/references/pgtool-record-read.md) 读出：结论与失败项（顶层）、测试项状态（`testItemDataCollection`）、错误码与执行标识（`rawEntity`）。
3. 判断失败性质：
   - `runState: Completed`、`verdict: Failed` 的项是实际判为失败的项。
   - `runState: Cancelled`、`verdict: None` 表示被取消，组按「必需项未通过」判为失败，不是测量超差。
   - 多个测试项在同一时刻被取消，通常是整次运行被中止（推测），根因看判为失败的那一项和 `rawEntity.errorCode`。
   - 有 `passed` 结果的项，可说明哪些步骤已通过。
4. 看是否稳定复现：取最近几条记录（`PageSize` 不宜超过 10，每条约 200KB 以上），比较失败项与错误码是否相同。
5. 需要执行层面的细节时，用 `rawEntity.identity` 进入路径 B。

## 路径 B：从部署与执行出发

1. 路径参数：`rawEntity.identity` 的 `ProjectId`、`DeploymentId`、`DeploymentDescriptorHash`；`executionId` 是 `OrchestratorInstanceId`（形如 `session-…`），`generation` 是 `OrchestratorGeneration`。`WorkflowExecutionId`（形如 `workflow-child-…`）是子流程执行，不是这里要的 `executionId`。没有记录时，用部署查活跃执行或最近执行得到 `executionId` 与 `generation`。
2. 读工作台：
   - 状态：`presentation.rootStatus`、`runtimeReadiness`、`state.summary`、`state.deviceSummary`。
   - 失败：`executionFailures`、`consistencyIssues`。
   - 会话绑定：`state.productionInfo`，即会话启动时绑定的工单、型号、生产配置。全为空表示会话没有绑定工单或生产配置。
   - 能否触发：`state.stations[].actions`、`state.triggers[].actions`（如 `canSubmit`）。
3. 需要细节时读调试快照：`occurrences` 中的 `failureCode`、`safeMessage`、`cancellationCause`；变量注意 `isRedacted`、`isTruncated`，不猜原值。
4. 工作台对应常驻会话，不是某一条记录；见 SKILL.md「会话与记录是两条时间线」。

## 路径 C：死信事件

- `sessionId` 留空取最近事件，可看到未能落库的节点事件、执行 ID 与原因。服务重启后可能为空。
- 用 `pgtool-flow` 的节点接口读失败节点，把节点 ID 翻译成步骤名称。

## 组合判读

| 同时看到 | 判读 |
|---|---|
| 工作台 `test-run-not-found` + 死信 `no-owner` + `state.productionInfo` 全空 | 会话没有绑定工单或生产配置，触发后结果落不了记录（报错与空绑定是确定的，因果为推测）。建议用户在界面停止会话，按工单重新启动 |
| 记录的测试项名称与工单型号明显不符 | 记录的型号取自工单，测试项来自实际运行的项目；说明本机实际跑的是另一个项目，请用户确认 |
| 最近几条记录失败在同一项、同一错误码 | 稳定复现，优先查该项涉及的设备与端口映射 |

## 诊断通道拿不到数据时

- 已结束的执行常返回 409 + `session-binding-not-found`，工作台与调试快照读不到。这是正常现象，不是路径写错：改走路径 A 或 C，并把该结果码作为线索写进回答。
- 通常能定位失败的运行与失败项；取消原因与变量级明细不一定拿得到，此时如实说明，请用户在界面查看。

## 回答要点

- 区分「确定」与「推测」：错误码与失败项是确定的；设备、接线、端口冲突等原因是推测，需要现场确认。
- 涉及处理动作（停止会话、重试、修改流程）时，说明由用户在界面操作。
