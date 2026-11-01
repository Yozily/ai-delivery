---
name: pgtool-record
version: 0.4.0
description: "PgTool 测试记录与统计：检索这台电脑的测试记录，读懂一条记录（结论、失败项、错误码、执行标识），本机记录条数统计；说明云端记录与全线统计的边界。用户问「最近的测试记录」「这条记录为什么判失败」「这周测了多少台」「合格率是多少」「云端能查到这条记录吗」时使用。不负责：同步上云（走 pgtool-sync）；执行过程与失败的完整诊断（走 pgtool-run）。"
metadata:
  requires:
    siblings: ["pgtool-shared"]
  product: PgTool
  product-version: "v3.0.1 之后的开发构建"
  observed-at: "2026-11-02"
  access: read-only
---

# record

**CRITICAL — 开始前先读 [`../pgtool-shared/SKILL.md`](../pgtool-shared/SKILL.md)：连接、两端、通用规则、返回与错误。** 没读到时至少遵守：只发 GET；结论附证据；云后台的问题不用本机数据回答。

## 两端

| 端 | 本域能做什么 |
|---|---|
| 客户端 | 这台电脑产生的测试记录：检索、读取、按型号与工单统计条数 |
| 云后台 | 云端记录、多台电脑汇总、全线统计与合格率。本版本无接口 |

用户问全线、其他电脑或云端的记录与统计时：说明属于云后台、当前看不到，请在云后台查看；可补充本机数据，但必须标明「仅这台电脑」。

## 场景速查

| 你要做的事 | 怎么做 | 动手前读 |
|---|---|---|
| 看最近的记录、某条记录的结论与失败项 | 记录检索，按三层读 | [pgtool-record-read.md](references/pgtool-record-read.md) |
| 本机测了多少 | 本机统计 | 本页「统计」 |
| 合格率、全线统计 | 云后台；本机只能给条数 | 本页「统计」 |
| 某条记录有没有传到云端 | 本机只能看同步队列 | `pgtool-sync` |

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

## 意图路由

| 用户想做什么 | 去哪里 |
|---|---|
| 记录内容、本机条数 | 本技能 |
| 测试为什么失败（需要执行层面的细节、是否稳定复现） | `pgtool-run`（[失败诊断](../pgtool-run/references/pgtool-run-diagnose.md)） |
| 记录为什么没传上云 | `pgtool-sync` |
