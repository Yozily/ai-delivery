# 读一条测试记录

记录检索 `Page=1&PageSize=1` 取最近一条；需要特定工单时加 `OrderNumber`。返回是信封，记录在 `data.value[0]`。

一条记录常超过 200KB，分三层读。

## 1. 顶层摘要

| 字段 | 含义 |
|---|---|
| `uid` | 记录 ID，与同步队列的 `recordId` 对应 |
| `sessionId` | `production-test:{deploymentId}:run:{runId}` |
| `orderNumber`、`productModel`、`operatorName` | 当时的工单、型号、操作员 |
| `isSuccess` | 是否合格 |
| `message` | 结论说明 |
| `errorItemName` | 失败的测试项名称 |
| `createTime` | 记录时间（本地时间） |
| `uploaded` | 含义未说明，不要据此判断是否已上传云端；同步情况看 `pgtool-sync` |

这些都是顶层字段，但 `isSuccess`、`errorItemName`、`createTime` 排在返回内容的末尾（约 237KB 处）。能解析完整 JSON 时直接取；工具只返回前一部分时会读不到，此时如实说明，请用户在界面核对记录结论。

## 2. 测试项：`testItemDataCollection`

JSON 字符串，需再解析一次，得到测试项数组。每项字段：`testItemId`、`testItemName`、`runState`、`verdict`、`applicability`、`isSuccess`、`message`、`errorSummary`、`evidenceSummary`、`measurements`、`startedAtUtc`、`completedAtUtc`。

- `runState: Completed`、`verdict: Failed`：该项实际判为失败。
- `runState: Cancelled`、`verdict: None`：被取消，不是测量超差。
- 有 `passed` 结果的项是已通过的步骤。

## 3. 内部实体：`rawEntity`

JSON 字符串，需再解析一次。

| 字段 | 含义 |
|---|---|
| `errorCode`、`errorMessage` | 失败的错误码与原文，定位根因最关键 |
| `startedAtUtc`、`completedAtUtc` | 运行起止（UTC） |
| `identity.ProjectId`、`identity.DeploymentId`、`identity.DeploymentDescriptorHash` | 进入执行诊断的路径参数 |
| `identity.OrchestratorInstanceId`、`identity.OrchestratorGeneration` | 执行诊断用的 `executionId`（`session-…`）与 `generation` |
| `identity.WorkflowExecutionId` | 子流程执行（`workflow-child-…`），不是执行诊断用的 `executionId` |
| `identity.StationId` | 工位 |

执行诊断见 `pgtool-run` 的失败诊断。
