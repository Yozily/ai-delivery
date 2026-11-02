# 测试记录与统计

## 两端

| 端 | 本域能做什么 |
|---|---|
| 客户端 | 这台电脑产生的测试记录：检索、读取、按型号与工单统计条数 |
| 云后台 | 云端记录、多台电脑汇总、全线统计与合格率。本版本无接口 |

用户问全线、其他电脑或云端的记录与统计时：说明属于云后台、当前看不到，请在云后台查看；可补充本机数据，但必须标明「仅这台电脑」。

## 接口（客户端）

| 用途 | 路径 | 体量 |
|---|---|---|
| 记录检索 | `/api/TestRecord/search?Page=&PageSize=&OrderNumber=&ProductModel=&SessionId=&StartTime=&EndTime=` | 大（每条可达数百 KB）；信封形态；按时间倒序；参数首字母大写；无单条读取接口 |
| 本机统计 | `/api/TestRecord/statistics?startTime=&endTime=` | 小；信封形态；参数首字母小写 |

## 核心概念

- 一条记录对应一次工位运行的终态；没有工位运行的空会话不产生记录。
- `sessionId` 形如 `production-test:{deploymentId}:run:{runId}`，从中可得到这次运行所用的部署。
- `productModel`、`orderNumber` 取自当时的工单，不是项目。按型号查记录为 0，不代表该项目没有记录。测试项名称与工单型号明显不符时，说明实际运行的是另一个项目，主动告诉用户。
- 记录的 `uid` 与同步队列的 `recordId` 对应。
- `createTime` 是本地时间；`rawEntity` 中的 `startedAtUtc`、`completedAtUtc` 是 UTC。

## 统计

- 本机统计按型号与工单只给记录条数 `count`，不分合格与不合格，所以**本机合格率也算不出来**。不要承诺合格率，也不要拿最近几条记录的抽样冒充统计。
- 本机统计只代表这台电脑，不是全线或云端结果。

## 读一条记录

记录检索 `Page=1&PageSize=1` 取最近一条（需要多条时最多 `PageSize=3`）；需要特定工单时加 `OrderNumber`。返回是信封，记录在 `data.value[0]`。

一条记录常超过 200KB，分三层读。

### 1. 顶层摘要

| 字段 | 含义 |
|---|---|
| `uid` | 记录 ID，与同步队列的 `recordId` 对应 |
| `sessionId` | `production-test:{deploymentId}:run:{runId}` |
| `orderNumber`、`productModel`、`operatorName` | 当时的工单、型号、操作员 |
| `isSuccess` | 是否合格 |
| `message` | 结论说明 |
| `errorItemName` | 失败的测试项名称 |
| `createTime` | 记录时间（本地时间） |
| `uploaded` | 含义未说明，不要据此判断是否已上传云端；同步情况看 [sync.md](sync.md) |

这些都是顶层字段，但 `isSuccess`、`errorItemName`、`createTime` 排在返回内容的末尾（约 237KB 处）。能解析完整 JSON 时直接取；工具只返回前一部分时会读不到，此时如实说明，请用户在界面核对记录结论。

### 2. 测试项：`testItemDataCollection`

JSON 字符串，需再解析一次，得到测试项数组。每项字段：`testItemId`、`testItemName`、`runState`、`verdict`、`applicability`、`isSuccess`、`message`、`errorSummary`、`evidenceSummary`、`measurements`、`startedAtUtc`、`completedAtUtc`。

- `runState: Completed`、`verdict: Failed`：该项实际判为失败。
- `runState: Cancelled`、`verdict: None`：被取消，不是测量超差。
- 有 `passed` 结果的项是已通过的步骤。

### 3. 内部实体：`rawEntity`

JSON 字符串，需再解析一次。

| 字段 | 含义 |
|---|---|
| `errorCode`、`errorMessage` | 失败的错误码与原文，定位根因最关键 |
| `startedAtUtc`、`completedAtUtc` | 运行起止（UTC） |
| `identity.ProjectId`、`identity.DeploymentId`、`identity.DeploymentDescriptorHash` | 进入执行诊断的路径参数 |
| `identity.OrchestratorInstanceId`、`identity.OrchestratorGeneration` | 执行诊断用的 `executionId`（`session-…`）与 `generation` |
| `identity.WorkflowExecutionId` | 子流程执行（`workflow-child-…`），不是执行诊断用的 `executionId` |
| `identity.StationId` | 工位 |

执行诊断见 [run-diagnose.md](run-diagnose.md)。
