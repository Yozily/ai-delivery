# 接口参考（只读）

PgTool 桌面端通过 HTTP 提供接口。下文路径都接在服务地址之后，服务地址由用户或管理员提供。本版本只使用 GET 读取接口。

体量为参考值，实际随数据量变化。如果你的工具对返回长度有限制，标「大」的接口可能只返回一部分，结论要说明这一点。

空列表或空字段不一定表示「没有」，也可能是未配置；说明时区分「接口返回为空」和「对象不存在」。

## 返回形态

不同接口的成功返回形态不同：

- 信封：`{code, message, length, data: {value, total}}`，如生产上下文、系统状态、记录检索。`length` 是本次返回条数，`total` 才是总数。
- 分页对象：`{items, total, page, pageSize}`，如同步列表。
- 裸数组或裸对象：如项目列表、部署列表、就绪、身份状态。

## 错误形态

| 形态 | 特征字段 | 处理 |
|---|---|---|
| 通用错误 | `type`、`title`、`status`、`traceId`，参数错误时带 `errors` | 按 `errors` 修正参数；404 表示对象不存在；向用户报告时带上 `traceId` |
| 信封 | `code`、`message`、`data` | `code` 为 0 表示成功 |
| 编辑诊断 | `message`、`diagnostics[{severity, code, path, message}]` | 按 `code` 与 `path` 定位 |
| 结果码 | `stage`、`outcomeCode` | 以 `not-found` 结尾表示当前没有该对象，不是故障 |
| 已下线 | `code: 410` 与替代说明 | 接口不可用，不要重试 |

## 环境

| 用途 | 路径 | 体量 |
|---|---|---|
| 服务是否就绪 | `/api/shell/readiness` | 小 |
| 产线身份 | `/api/iot-product-production/identity/status` | 小 |
| 当前生产上下文（工单、型号、操作员） | `/api/production-context` | 小 |
| 系统资源 | `/api/SystemStatus/status` | 小 |
| 产品型号 | `/api/production-context/product-models?productModel=&limit=` | 小 |

## 流程内容

| 用途 | 路径 | 体量 |
|---|---|---|
| 项目列表 | `/api/testflow-projects` | 大（每项 200–400KB，含完整流程定义） |
| 项目中的工作流 | `/api/testflow-projects/{projectId}/workflow-editing/workflows` | 小 |
| 工作流大纲 | `/api/testflow-projects/{projectId}/workflow-editing/outline?workflowId=&depth=` | 小；必须带 `workflowId`；`childCount` 大于 0 而未展开时需加大 `depth` |
| 单个节点 | `/api/testflow-projects/{projectId}/workflow-editing/node?workflowId=&nodeId=&view=` | 小 |
| 节点类型 | `/api/workflow-editing/node-types?q=&category=`；详情 `/api/workflow-editing/node-types/detail?type=` | 中 |
| 表达式规则 | `/api/workflow-expressions/profile` | 小 |
| 部署列表 | `/api/testflow-deployments` | 大（约 550KB）；按部署 ID 排序；不分页；`projectId`、`limit` 不报错也不生效；只能当索引，不能用来判断最新 |
| 单个部署 | `/api/testflow-deployments/{deploymentId}` | 小（约 4KB）；含 `deployedAt`、`status`、`releaseAvailability`、`appliedLocalBindings.devicePortMappings` |

## 执行与诊断

先从部署中取 `deploymentId`、`workflow.productionTestId`、`workflow.deploymentDescriptorHash`（本版本中 `productionTestId` 通常与 `deploymentId` 相同，仍以部署返回值为准）。`{h}` 必填，漏传返回 400。以下 `{pt}` 表示 `/api/production-workflow/projects/{projectId}/deployments/{deploymentId}/production-tests/{productionTestId}`，`{h}` 表示 `expectedDeploymentDescriptorHash={deploymentDescriptorHash}`。

| 用途 | 路径 | 体量 |
|---|---|---|
| 活跃执行 | `{pt}/active-execution?{h}` | 小 |
| 最近执行 | `{pt}/recent-execution?{h}` | 小 |
| 工作台 | `{pt}/executions/{executionId}/{generation}/workbench?{h}` | 中（约 45KB） |
| 调试快照 | `{pt}/executions/{executionId}/{generation}/debug?{h}` | 中（约 35KB） |
| 执行状态 | `/api/production-workflow/projects/{projectId}/executions/{executionId}/{generation}` | 小 |
| 死信事件 | `/api/automation/node-lifecycle/dead-letters?sessionId=&limit=` | 小；`sessionId` 可留空取全部最近事件；部署定位不到时的诊断备用入口 |

工作台先看 `presentation.rootStatus`、`state.summary`、`executionFailures`、`consistencyIssues`、`state.deviceSummary`。调试快照看 `occurrences` 中的 `failureCode`、`safeMessage`、`cancellationCause`，变量注意 `isRedacted`、`isTruncated`。

## 记录与同步

| 用途 | 路径 | 体量 |
|---|---|---|
| 同步汇总 | `/api/test-record-sync/summary` | 小；只有各状态数量，不含错误码分组 |
| 同步列表 | `/api/test-record-sync?page=&pageSize=&status=` | 小；按时间升序，最新在最后一页；`pageSize` 可到 50；无时间过滤；`recordCreatedAt` 为本地时间 |
| 记录检索 | `/api/TestRecord/search?Page=&PageSize=&OrderNumber=&ProductModel=&SessionId=&StartTime=&EndTime=` | 大（每条可达数百 KB）；按时间倒序；`sessionId` 形如 `production-test:{deploymentId}:run:{runId}`；`productModel` 取自工单；结论字段在记录末尾，截断时常读不到；无单条读取接口 |
| 统计 | `/api/TestRecord/statistics?startTime=&endTime=` | 小 |
