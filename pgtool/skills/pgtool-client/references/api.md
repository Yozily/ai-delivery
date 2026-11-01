# 客户端接口参考（只读）

以下都是 PgTool 客户端（桌面产测端）在本机 `http://127.0.0.1:10532` 提供的接口，下文路径都接在这个地址之后。数据只代表这台电脑；云后台的接口不在本技能范围。本版本只使用 GET 读取接口。

体量为参考值，实际随数据量变化。如果你的工具对返回长度有限制，标「大」的接口可能只返回一部分，结论要说明这一点。

空列表或空字段不一定表示「没有」，也可能是未配置；说明时区分「接口返回为空」和「对象不存在」。

## 返回形态

不同接口的成功返回形态不同：

- 信封：`{code, message, length, data: {value, total}}`，如生产上下文、系统状态、记录检索。`length` 是本次返回条数，`total` 才是总数。
- 分页对象：`{items, total, page, pageSize}`，如同步列表。
- 带版本的结果：`{revision, value}`，如工作流列表、大纲。`revision` 在顶层，形如 `<哈希>:<时间>`，冒号后是项目内容最后修改时间；内容在 `value`。
- 裸数组或裸对象：如项目列表、部署列表、就绪、身份状态。
- 结果码：`{stage, outcomeCode, …}`，如活跃执行、最近执行；HTTP 状态码可能是 404 或 409，见 errors.md。

## 错误

错误形态、结果码与错误码见 errors.md。

## 环境

| 用途 | 路径 | 体量 |
|---|---|---|
| 服务是否就绪 | `/api/shell/readiness` | 小 |
| 产线身份（这台电脑） | `/api/iot-product-production/identity/status` | 小 |
| 当前生产上下文（工单、型号、操作员） | `/api/production-context` | 小 |
| 系统资源 | `/api/SystemStatus/status` | 小 |
| 产品型号 | `/api/production-context/product-models?productModel=&limit=` | 小 |

## 流程内容

| 用途 | 路径 | 体量 |
|---|---|---|
| 项目列表 | `/api/testflow-projects` | 大（每项 200–400KB，含完整流程定义）；项目标识字段是 `projectId`，另有 `name`、`description` |
| 项目中的工作流 | `/api/testflow-projects/{projectId}/workflow-editing/workflows` | 小 |
| 工作流大纲 | `/api/testflow-projects/{projectId}/workflow-editing/outline?workflowId=&depth=` | 小；必须带 `workflowId`；根节点在 `value.root`，节点字段为 `id`、`kind`、`name`、`children`、`childCount`；`childCount` 大于 0 而未展开时需加大 `depth` |
| 单个节点 | `/api/testflow-projects/{projectId}/workflow-editing/node?workflowId=&nodeId=&view=` | 小 |
| 节点类型 | `/api/workflow-editing/node-types?q=&category=`；详情 `/api/workflow-editing/node-types/detail?type=` | 中 |
| 表达式规则 | `/api/workflow-expressions/profile` | 小 |
| 部署列表 | `/api/testflow-deployments` | 大（约 550KB，数百条）；按部署 ID 排序；不分页；`projectId`、`limit` 不报错也不生效；历史部署通常也是 `active`；只能当索引，不能用来判断最新或当前 |
| 单个部署 | `/api/testflow-deployments/{deploymentId}` | 小（约 4KB）；含 `deployedAt`、`status`、`releaseAvailability`、`appliedLocalBindings.devicePortMappings` |

## 执行与诊断

先从部署中取 `deploymentId`、`workflow.productionTestId`、`workflow.deploymentDescriptorHash`（本版本中 `productionTestId` 通常与 `deploymentId` 相同，仍以部署返回值为准）。`{h}` 必填，漏传返回 400。以下 `{pt}` 表示 `/api/production-workflow/projects/{projectId}/deployments/{deploymentId}/production-tests/{productionTestId}`，`{h}` 表示 `expectedDeploymentDescriptorHash={deploymentDescriptorHash}`。

| 用途 | 路径 | 体量 |
|---|---|---|
| 活跃执行 | `{pt}/active-execution?{h}` | 小；必须先知道部署；没有「列出全部活跃执行」的接口 |
| 最近执行 | `{pt}/recent-execution?{h}` | 小 |
| 工作台 | `{pt}/executions/{executionId}/{generation}/workbench?{h}` | 中（约 45KB） |
| 调试快照 | `{pt}/executions/{executionId}/{generation}/debug?{h}` | 中（约 35KB） |
| 执行状态 | `/api/production-workflow/projects/{projectId}/executions/{executionId}/{generation}` | 小 |
| 死信事件 | `/api/automation/node-lifecycle/dead-letters?sessionId=&limit=` | 小；`sessionId` 可留空取全部最近事件；部署定位不到时的诊断备用入口 |

读法见 diagnosis.md。

## 记录与同步

| 用途 | 路径 | 体量 |
|---|---|---|
| 同步汇总 | `/api/test-record-sync/summary` | 小；只有各状态数量，不含错误码分组 |
| 同步列表 | `/api/test-record-sync?page=&pageSize=&status=` | 小；按时间升序，最新在最后一页；`pageSize` 可到 50；无时间过滤；`recordCreatedAt` 为本地时间 |
| 记录检索 | `/api/TestRecord/search?Page=&PageSize=&OrderNumber=&ProductModel=&SessionId=&StartTime=&EndTime=` | 大（每条可达数百 KB）；按时间倒序；`sessionId` 形如 `production-test:{deploymentId}:run:{runId}`；`productModel` 取自工单；结论字段在记录末尾，截断时常读不到；`testItemDataCollection` 与 `rawEntity` 是 JSON 字符串，需再解析；无单条读取接口；参数首字母大写 |
| 本机统计 | `/api/TestRecord/statistics?startTime=&endTime=` | 小；只统计这台电脑的记录，不是云端统计；按型号与工单只给记录条数 `count`，不分合格与不合格；参数首字母小写 |
