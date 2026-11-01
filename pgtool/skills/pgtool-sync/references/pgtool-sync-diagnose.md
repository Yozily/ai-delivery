# 记录为什么没同步到云后台

只读诊断。按「现象、影响范围、证据、可能原因、建议下一步」回答。

## 步骤

1. **读同步汇总**，得到各同步状态的数量。汇总不含错误码分组。只有一种状态且总数不大时，直接翻完所有页。
2. **找最新的条目**：同步列表按记录时间升序排列，第 1 页是最早的，最新的在最后一页。用汇总的 `total` 算出最后一页（例如 `total` 120、`pageSize` 50，最后一页是第 3 页）。
3. **按错误码归纳**：按 `lastErrorCode` 和时间分组计数；同一错误码可能对应不同原因，不同错误码也可能用相同的 `lastErrorReason` 文案，计数以 `lastErrorCode` 为准。对照下方错误码表给出处理方。
4. **当前与历史分开说**：生产上下文的 `cloudSync.lastError` 是这台电脑最近一次连接云后台的结果，可能与队列里最后一条失败原因不同。
5. **对照记录**：同步条目的 `recordId` 与测试记录的 `uid` 对应。
6. **时间**：`recordCreatedAt` 没有时区标记（本地时间），与 UTC 时间比较时要注意。

## 同步条目字段

| 字段 | 含义 |
|---|---|
| `recordId`、`sessionId`、`orderNumber`、`productModel`、`isSuccess` | 对应的测试记录 |
| `recordCreatedAt` | 记录时间（本地时间） |
| `syncStatus` | 同步状态；`PermanentFailure` 表示自动重试已用完，不会再自动传，问题修好后需用户在界面手动重试 |
| `attemptCount` | 自动尝试次数 |
| `manualRetryCount` | 手动重试次数，0 表示从未手动重试 |
| `lastErrorCode`、`lastErrorReason` | 最后一次失败的错误码与原文 |
| `declaredProductionComputerId` | 上传时申报的产线电脑标识，可能缺失 |

`declaredProductionComputerId` 与身份状态中本机的电脑标识不同，说明这些记录申报的是另一个产线身份（例如这台电脑的身份变更过），可能影响上传权限；作为线索报告，请管理员核对。不能据此推断其他电脑的上传情况。

## 同步错误码（lastErrorCode）

| 错误码 | 含义 | 找谁 | 重试 |
|---|---|---|---|
| `remote_unavailable` | 云后台不可达（连接被拒、网关 502 等，看 `lastErrorReason`） | 运维 | 修好后手动重试 |
| `identity_provider_unavailable` | 身份服务发不出机器令牌 | 身份服务管理员 | 修好后手动重试 |
| `identity_provider_rejected` | 身份服务拒绝签发 | 身份服务管理员 | 修好后手动重试 |
| `identity_provider_rate_limited` | 身份服务限流，本身是临时问题 | 无需找人 | 稍后手动重试 |
| `invalid_client` | 机器凭据已失效 | 平台管理员 | 修好后手动重试 |
| `machine_credential_unavailable` | 机器凭据缺失 | 平台管理员 | 修好后手动重试 |
| `forbidden` | 凭据没有上传权限 | 平台管理员 | 修好后手动重试 |

## 建议顺序

先处理云后台可达（运维），再处理凭据与身份服务；修好后由用户在界面按原因分批重试。

程度：可做；精确的按错误码计数需翻完所有页。
