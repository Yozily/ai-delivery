---
name: pgtool-flow
version: 0.4.0
description: "PgTool 测试流程：查看测试项目、工作流、流程大纲与节点配置；判断某项目在这台电脑上部署的是否为最新内容；给出修改流程参数的建议。用户问「某项目主流程有哪些步骤」「这个节点怎么配置的」「部署的是不是最新」「把某参数改成某值」时使用。不负责：运行状态、能否开测与失败原因（走 pgtool-run）；测试记录（走 pgtool-record）。本版本不直接修改流程。"
metadata:
  requires:
    siblings: ["pgtool-shared"]
  product: PgTool
  product-version: "v3.0.1 之后的开发构建"
  observed-at: "2026-11-02"
  access: read-only
---

# flow

**CRITICAL — 开始前先读 [`../pgtool-shared/SKILL.md`](../pgtool-shared/SKILL.md)：连接、两端、通用规则、返回与错误。** 没读到时至少遵守：只发 GET；结论附证据；云后台的问题不用本机数据回答。

## 两端

| 端 | 本域能做什么 |
|---|---|
| 客户端 | 测试流程的编辑、发布与部署都在客户端：可读项目、工作流、大纲、节点、部署 |
| 云后台 | 不涉及 |

## 场景速查

按当前要做的事选行，动手前先读该行的 reference。

| 你要做的事 | 怎么做 | 动手前读 |
|---|---|---|
| 看流程有哪些步骤 | 项目 → 工作流列表 → 大纲 → 必要时节点 | [pgtool-flow-read.md](references/pgtool-flow-read.md) |
| 判断部署的是否为最新内容 | 工作流 `revision` 时间；本机在用的部署；该项目最晚的部署 | [pgtool-flow-deployment.md](references/pgtool-flow-deployment.md) |
| 改某个步骤的参数 | 定位节点后给出修改建议 | 本页「修改建议」 |

## 接口（客户端）

路径接在 `http://127.0.0.1:10532` 之后。

| 用途 | 路径 | 体量 |
|---|---|---|
| 项目列表 | `/api/testflow-projects` | 大（每项 200–400KB，含完整流程定义）；裸数组；项目标识字段是 `projectId`，另有 `name`、`description` |
| 项目中的工作流 | `/api/testflow-projects/{projectId}/workflow-editing/workflows` | 小；`{revision, value}`，`revision` 在顶层 |
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

## 意图路由

| 用户想做什么 | 去哪里 |
|---|---|
| 流程步骤、节点配置、部署是否最新、改参数 | 本技能 |
| 本机当前在运行哪个流程、能否开测、为什么失败 | `pgtool-run` |
| 某次运行的结果 | `pgtool-record` |
