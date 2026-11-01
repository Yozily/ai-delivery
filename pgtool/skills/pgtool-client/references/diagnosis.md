# 诊断

两类常见问题：测试为什么失败、记录为什么没同步到云后台。都只读，按「现象、影响范围、证据、可能原因、建议下一步」回答。错误与结果码的含义见 errors.md。

## 1. 测试为什么失败

依次尝试以下路径，哪条通用哪条。

### 路径 A：从测试记录出发（最常用）

1. 记录检索 `Page=1&PageSize=1` 取最近一条记录；需要特定工单时加 `OrderNumber`。
2. 记录很大（常超过 200KB），分三层读：
   - **顶层摘要**：`uid`、`sessionId`、`orderNumber`、`productModel`、`operatorName`、`isSuccess`、`message`、`errorItemName`、`createTime`。都是顶层字段，但 `isSuccess`、`errorItemName`、`createTime` 排在返回内容的末尾：能解析完整 JSON 时直接取；工具只返回前一部分时会读不到，此时如实说明，请用户在界面核对记录结论。
   - **`testItemDataCollection`**：JSON 字符串，需再解析一次，得到测试项数组。
   - **`rawEntity`**：JSON 字符串，需再解析一次。其中 `errorCode`、`errorMessage` 是失败的错误码与原文，`startedAtUtc`、`completedAtUtc` 是 UTC 时间，`identity` 含定位执行用的标识（见第 4 步）。
3. 测试项看 `runState`、`verdict`、`isSuccess`、`message`、`errorSummary`：
   - `runState: Completed`、`verdict: Failed` 是该项实际判为失败。
   - `runState: Cancelled`、`verdict: None` 表示被取消，组按「必需项未通过」判为失败，不是测量超差。
   - 多个测试项在同一时刻被取消，通常是整次运行被中止（推测），根因看判为失败的那一项和 `rawEntity.errorCode`。
   - 测量项有 `passed` 等结果时，可说明哪些步骤已通过。
4. 定位执行：`rawEntity.identity` 中 `ProjectId`、`DeploymentId`、`DeploymentDescriptorHash` 用于路径 B 的路径参数；路径 B 的 `executionId` 是 `OrchestratorInstanceId`（形如 `session-…`），`generation` 是 `OrchestratorGeneration`。`WorkflowExecutionId`（形如 `workflow-child-…`）是子流程执行，不是路径 B 要的 `executionId`。
5. 看是否稳定复现：取最近几条记录（`PageSize` 不宜超过 10，每条约 200KB 以上），比较失败项与错误码是否相同。
### 路径 B：从部署与执行出发

1. 用部署 ID 与部署描述哈希取活跃执行，没有则取最近执行，得到 `executionId` 与 `generation`。
2. 读工作台：`presentation.rootStatus`、`state.summary`、`executionFailures`、`consistencyIssues`、`state.deviceSummary`。
3. 需要细节时读调试快照：`occurrences` 中的 `failureCode`、`safeMessage`、`cancellationCause`；变量注意 `isRedacted`、`isTruncated`，不猜原值。

**会话与记录是两条时间线。** 测试流程的主流程常驻运行：启动一次后循环等待触发（活跃执行 `runtimeStatus: Waiting`、工作台 `rootStatus: waitingForTrigger` 是正常状态，不是卡住）。每触发一次产生一条测试记录。工作台的 `executionFailures` 累积了这个常驻会话里多次触发的失败，不等于某一条记录的失败；按时间对照，不要把两者当成同一次运行。
### 路径 C：死信事件

- `sessionId` 留空取最近事件，可看到未能落库的节点事件、执行 ID 与原因。服务重启后可能为空。
- 用节点接口读失败节点，把节点 ID 翻译成步骤名称。

### 诊断通道拿不到数据时

- 工作台、调试快照或执行状态返回诊断类结果码（见 errors.md 第 2 节）时，换一条路径继续，并把该结果码作为线索写进回答。
- 通常能定位失败的运行与失败组；取消原因与子项明细不一定拿得到，此时如实说明并请用户在界面查看。

## 2. 记录为什么没同步到云后台

同步队列在客户端，失败原因常在云后台或身份服务一侧。你只能看到这台电脑的队列，看不到云后台是否已有某条记录。

1. 读同步汇总，得到各同步状态的数量。汇总不含错误码分组。只有一种状态且总数不大时，直接翻完所有页。
2. 同步列表按记录时间升序排列，第 1 页是最早的，最新的在最后一页。用汇总的 `total` 算出最后一页（例如 `total` 120、`pageSize` 50，最后一页是第 3 页）。
3. 按 `lastErrorCode` 和时间归纳；同一错误码可能对应不同原因，看 `lastErrorReason`。错误码与处理方见 errors.md 第 4 节。
4. `cloudSync.lastError`（生产上下文中）是这台电脑最近一次连接云后台的结果，只有错误码，没有时间与原因原文；可能与队列里最后一条失败原因不同，两者分开说。
5. 同步条目的 `recordId` 与测试记录的 `uid` 对应。某条记录未出现在同步列表中时，接口没有说明原因，如实告诉用户，不要断言丢失。
6. 同步列表的 `recordCreatedAt` 没有时区标记（本地时间），与带 `+00:00` 的 UTC 时间比较时要注意。
7. 记录的 `productModel` 取自当时的工单，不是项目。按型号查记录为 0，不代表该项目没有记录。
8. `PermanentFailure` 表示自动重试已用完，不会再自动传；问题修好后仍需用户在界面手动重试。原因不同的记录建议分批重试。
9. 同步条目字段：`recordId`、`sessionId`、`productModel`、`orderNumber`、`isSuccess`、`recordCreatedAt`、`syncStatus`、`attemptCount`（自动尝试次数）、`lastErrorCode`、`lastErrorReason`、`manualRetryCount`（手动重试次数，0 表示从未手动重试）、`declaredProductionComputerId`（上传时申报的产线电脑标识，可能缺失）。
10. `declaredProductionComputerId` 与身份状态中本机的电脑标识不同，说明这些记录申报的是另一个产线身份（例如这台电脑的身份变更过），可能影响上传权限；作为线索报告，请管理员核对。不能据此推断其他电脑的上传情况。

程度：可做；精确的按错误码计数需翻完所有页。
