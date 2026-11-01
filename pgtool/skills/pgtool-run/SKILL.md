---
name: pgtool-run
version: 0.4.0
description: "PgTool 测试运行：查看测试会话与执行状态、工作台、调试快照、死信事件；检查能不能开始测试；诊断测试为什么失败。用户问「能不能测」「帮我启动测试」「当前测试为什么失败」「工位是不是卡住了」「现在在跑哪个流程」时使用。不负责：流程内容与部署是否最新（走 pgtool-flow）；记录检索与统计（走 pgtool-record）。本技能不启动、停止、终止或重试测试。"
metadata:
  requires:
    siblings: ["pgtool-shared"]
  product: PgTool
  product-version: "v3.0.1 之后的开发构建"
  observed-at: "2026-11-02"
  access: read-only
---

# run

**CRITICAL — 开始前先读 [`../pgtool-shared/SKILL.md`](../pgtool-shared/SKILL.md)：连接、两端、通用规则、返回与错误。** 没读到时至少遵守：只发 GET；结论附证据；云后台的问题不用本机数据回答。

**你不能启动、停止、终止或重试测试。** 即使条件全部满足，也请用户在 PgTool 界面操作。

## 两端

| 端 | 本域能做什么 |
|---|---|
| 客户端 | 测试会话与执行都在客户端：可读活跃执行、最近执行、工作台、调试快照、执行状态、死信事件 |
| 云后台 | 不涉及 |

## 场景速查

| 你要做的事 | 怎么做 | 动手前读 |
|---|---|---|
| 能不能测、帮我启动 | 按清单逐项检查，给出三选一结论，请用户在界面启动 | [pgtool-run-preflight.md](references/pgtool-run-preflight.md) |
| 测试为什么失败 | 从最近测试记录出发，再到执行与工作台，必要时看死信 | [pgtool-run-diagnose.md](references/pgtool-run-diagnose.md) |
| 现在在跑哪个流程 | 最近记录 → 部署 → 活跃执行 → 部署的 `projectId` | 本页「找本机在用的执行」 |

## 接口（客户端）

先从单个部署（见 `pgtool-flow`）取 `projectId`、`deploymentId`、`workflow.productionTestId`、`workflow.deploymentDescriptorHash`。`productionTestId` 通常与 `deploymentId` 相同，仍以部署返回值为准。

以下 `{pt}` 表示 `/api/production-workflow/projects/{projectId}/deployments/{deploymentId}/production-tests/{productionTestId}`，`{h}` 表示 `expectedDeploymentDescriptorHash={deploymentDescriptorHash}`；`{h}` 必填，漏传返回 400。

| 用途 | 路径 | 体量 |
|---|---|---|
| 活跃执行 | `{pt}/active-execution?{h}` | 小；结果码形态；没有活跃执行时返回 404 + `not-found`，属正常 |
| 最近执行 | `{pt}/recent-execution?{h}` | 小；没有时返回 404 + `recent-not-found`，属正常 |
| 工作台 | `{pt}/executions/{executionId}/{generation}/workbench?{h}` | 中（约 45KB） |
| 调试快照 | `{pt}/executions/{executionId}/{generation}/debug?{h}` | 中（约 35KB） |
| 执行状态 | `/api/production-workflow/projects/{projectId}/executions/{executionId}/{generation}` | 小 |
| 死信事件 | `/api/automation/node-lifecycle/dead-letters?sessionId=&limit=` | 小；`sessionId` 可留空取最近事件；服务重启后可能为空 |

没有「列出全部执行」或「列出全部活跃执行」的接口，必须先知道部署。

## 核心概念

- **会话（执行）**：`executionId` 形如 `session-…`，配合 `generation` 使用。测试流程的主流程常驻运行：启动一次后循环等待触发。
- **`Waiting` 是正常状态。** 活跃执行 `runtimeStatus: Waiting`、工作台 `presentation.rootStatus: waitingForTrigger` 表示会话在等下一次触发，不是卡住。
- **会话与记录是两条时间线。** 每触发一次产生一条测试记录。工作台的 `executionFailures` 累积了这个常驻会话里多次触发的失败，不等于某一条记录的失败；按时间对照，不要把两者当成同一次运行。
- **三种操作不同**：停止会话、终止工位、重试。都由用户在界面操作。

## 找本机在用的执行

1. 按 `pgtool-record` 读最近一条测试记录，从 `sessionId`（`production-test:{deploymentId}:run:{runId}`）得到部署 ID。
2. 按 `pgtool-flow` 读该单个部署，得到 `projectId` 与路径参数。
3. 查活跃执行。有结果（如 `Waiting`）即本机正在用这条部署；返回 `not-found` 说明这条部署当前没有活跃执行，其他部署是否有，未知。

## 执行失败码

工作台 `executionFailures`、调试快照 `failureCode` 与死信事件中可能出现。测试流程中的断言也可以自定义失败码，含义以随附的消息为准。

| 失败码 | 含义 | 处理 |
|---|---|---|
| `production-testing.test-item-result.test-run-not-found` | 无法记录测试结果：当前执行没有关联到测试记录 | 转述消息中的建议（停止本次测试，检查工位会话的创建与绑定）；停止测试需用户在界面操作 |
| `client-subapp.ownership.unknown:no-owner`（死信原因） | 节点事件无法归属到工位会话，未能落库 | 作为线索报告：工位会话的归属缺失 |

## 意图路由

| 用户想做什么 | 去哪里 |
|---|---|
| 能不能测、启动、为什么失败、在跑哪个流程 | 本技能 |
| 当前工单、产线身份、产品定义绑定 | `pgtool-production` |
| 流程步骤、部署是否最新 | `pgtool-flow` |
| 某条记录的结论与测试项 | `pgtool-record` |
