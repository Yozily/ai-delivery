---
name: pgtool-production
version: 0.4.0
description: "PgTool 生产现场：查看当前工单、产品型号、计划数量、操作员、工单是否有效、产线身份状态、产品定义与生产配置是否已绑定、系统资源。用户问「这台电脑在做哪个工单」「产线身份正常吗」「产品定义绑了没有」「这台电脑的状态」时使用。不负责：能不能开测、启动测试（走 pgtool-run，它会用到本技能的数据）；记录为什么没同步（走 pgtool-sync）。"
metadata:
  requires:
    siblings: ["pgtool-shared"]
  product: PgTool
  product-version: "v3.0.1 之后的开发构建"
  observed-at: "2026-11-02"
  access: read-only
---

# production

**CRITICAL — 开始前先读 [`../pgtool-shared/SKILL.md`](../pgtool-shared/SKILL.md)：连接、两端、通用规则、返回与错误。** 没读到时至少遵守：只发 GET；结论附证据；云后台的问题不用本机数据回答。

## 两端

| 端 | 本域能做什么 |
|---|---|
| 客户端 | 读这台电脑当前的工单、型号、操作员、产线身份状态，以及产品定义与生产配置是否已绑定 |
| 云后台 | 产线身份登记、产品定义管理、工单下发。本版本无接口，请用户在云后台查看或处理 |

## 接口（客户端）

路径接在 `http://127.0.0.1:10532` 之后。

| 用途 | 路径 | 体量 |
|---|---|---|
| 服务是否就绪 | `/api/shell/readiness` | 小 |
| 产线身份（这台电脑） | `/api/iot-product-production/identity/status` | 小；`status` 为 `active` 表示正常；含本机的产线电脑标识 |
| 当前生产上下文 | `/api/production-context` | 小；信封形态 |
| 系统资源 | `/api/SystemStatus/status` | 小；信封形态 |
| 产品型号目录 | `/api/production-context/product-models?productModel=&limit=` | 小；当前返回空，不能用来核对型号 |

## 读生产上下文

| 字段 | 含义 |
|---|---|
| `orderNumber` | 工单号 |
| `productModel` | 产品型号（来自工单） |
| `orderQuantity` | 计划数量 |
| `operatorName` | 操作员 |
| `orderValid` | 工单是否有效 |
| `productDefinition`、`productionConfig` | `id`、`version`、`releaseId`、`digest` 全为空串表示尚未绑定，可能影响能否测试，应提示用户（影响程度标为推测） |
| `cloudSync.lastError` | 这台电脑最近一次连接云后台的结果，只有错误码、没有时间；原因排查走 `pgtool-sync` |

## 规则

1. 只说这台电脑的状态。工单、身份是本机视角，不代表整条线。
2. 工单型号与流程项目之间没有字段关联，不要凭项目名称断言相符或不符。需要核对时走 `pgtool-run` 的开测前检查。
3. 产品定义、产线身份的修改在云后台，不在本技能范围。

## 意图路由

| 用户想做什么 | 去哪里 |
|---|---|
| 这台电脑在做哪个工单、身份与绑定状态 | 本技能 |
| 能不能测、帮我启动 | `pgtool-run`（[开测前检查](../pgtool-run/references/pgtool-run-preflight.md)） |
| `cloudSync.lastError` 有值，记录传不上去 | `pgtool-sync` |
| 修改产品定义、登记产线身份 | 云后台，本版本无接口 |
