# 测试流程

## 两端

| 端 | 本域能做什么 |
|---|---|
| 客户端 | 测试流程的编辑、发布与部署都在客户端：可读项目、工作流、大纲、节点、部署 |
| 云后台 | 不涉及 |

## 接口（客户端）

路径接在 `http://127.0.0.1:10532` 之后。

| 用途 | 路径 | 体量 |
|---|---|---|
| 项目列表 | `/api/testflow-projects` | 大（每项 200–400KB，含完整流程定义）；裸数组；项目标识字段是 `projectId`，另有 `name`、`description` |
| 项目中的工作流 | `/api/testflow-projects/{projectId}/workflow-editing/workflows` | 小；`{revision, value}`，`revision` 在顶层；`value` 是工作流数组，每项含 `workflowId`、`name`、`isEntry` |
| 工作流大纲 | `/api/testflow-projects/{projectId}/workflow-editing/outline?workflowId=&depth=` | 小；必须带 `workflowId`；根节点在 `value.root` |
| 单个节点 | `/api/testflow-projects/{projectId}/workflow-editing/node?workflowId=&nodeId=&view=` | 小；`view` 只能是 `source`（作者填写）、`effective`（生效值）、`origin`（每个值来自哪一层）；配置在 `value.configuration` |
| 节点类型 | `/api/workflow-editing/node-types?q=&category=`；详情 `/api/workflow-editing/node-types/detail?type=` | 中 |
| 表达式规则 | `/api/workflow-expressions/profile` | 小 |
| 部署列表 | `/api/testflow-deployments` | 大（约 550KB，数百条）；按部署 ID 排序；不分页；`projectId`、`limit` 不报错也不生效 |
| 单个部署 | `/api/testflow-deployments/{deploymentId}` | 小（约 4KB）；含 `projectId`、`deployedAt`、`status`、`releaseAvailability`、`workflow.productionTestId`、`workflow.deploymentDescriptorHash`、`appliedLocalBindings.devicePortMappings` |

## 核心概念

- **项目**：一套测试方案，含多个工作流。项目是作者态，正在编辑的内容。
- **入口工作流**：工作流列表中 `isEntry: true` 的那个。它常是常驻骨架（循环等待触发、派发），真正的测试步骤在被派发的工作流里。
- **大纲节点**：字段为 `id`、`kind`、`name`、`children`、`childCount`；派发与调用节点另有 `targetWorkflowId`。`kind` 为 `catch`、`finally`、`return` 的不是测试步骤。
- **`revision`**：形如 `<哈希>:<时间>`，冒号后是项目内容最后修改时间。
- **发布与部署**：发布是不可变版本；部署是发布在这台电脑上的落地，带本地设备绑定。`status: active` 只说明部署记录有效，不等于正在使用。
- **设备绑定**：单个部署的 `appliedLocalBindings.devicePortMappings` 列出逻辑设备到串口等端口的映射。两个设备映射到同一个端口时要特别指出，可能导致读写超时（推测，需现场确认）。

## 修改建议

本版本不直接修改流程。用户要改某个参数时：

1. 用大纲和节点定位该步骤，向用户确认是哪一个节点。
2. 给出修改建议：节点 ID 与名称、字段、原值、新值。
3. 说明修改后需要发布并部署，才会在产线生效；请用户在流程编辑器中修改。

## 看流程步骤

问题举例：「某项目的主流程有哪些步骤？」

### 步骤

1. **定位项目 ID**（字段 `projectId`）。项目列表很大，常常读不全。用户常用描述性的叫法，不是项目名称。按用户的说法先匹配 `name`，匹配不到再看 `description`。命中多个时（例如只差「并行」后缀的两个版本），列出候选（名称与 ID）；能继续时说明你按哪一个回答，并提醒用户另一个的区别。用户能直接给出项目 ID 时跳过这一步。
2. **读工作流列表**（工作流在 `value` 中），找到入口工作流（`isEntry: true`）。
3. **读大纲**：先用 `depth=3` 看规模；如果最深一层仍有 `childCount` 大于 0 而未展开，直接改用 `depth=10` 一次读全。
4. **跟进派发**：入口工作流常是多层骨架（并行、循环、等待触发、派发），真正的测试步骤在被派发的工作流里（例如「测试调度」）。大纲中 `kind: dispatchWorkflow`（派发）与 `kind: call`（调用）的节点带 `targetWorkflowId`，用它读目标工作流的大纲。不要按名称猜，名称相近的工作流很多。
5. **排顺序**：步骤顺序按大纲中 `children` 的先后。
6. **分出收尾**：`catch`（异常收尾）、`finally`（收尾）、`return` 不是测试步骤，单独列为收尾。
7. `loop` 里套着等待触发，表示每测一台都重新等待触发。
8. 需要某一步的具体参数时，再用节点接口读该节点，`view=effective`（生效值）。参数值有三种写法：直接值；`[cel]` 开头的表达式；`{op, type, value}` 或 `{op: "slot", …}` 形式的引用（`op: literal` 时 `value` 即值）。
9. 大纲根节点（`id` 为 `$workflow-root`）的 `name` 可能为空，工作流名称以工作流列表为准。

### 注意

- 项目的 `description` 是作者填写的说明，可能过期；以大纲为准，发现不一致时告诉用户。
- 不要读整份项目定义来找步骤，用大纲。

程度：可做。
