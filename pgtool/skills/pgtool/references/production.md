# 生产现场

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
| `cloudSync.lastError` | 这台电脑最近一次连接云后台的结果，只有错误码、没有时间；原因排查走 [sync.md](sync.md) |

## 规则

1. 只说这台电脑的状态。工单、身份是本机视角，不代表整条线。
2. 工单型号与流程项目之间没有字段关联，不要凭项目名称断言相符或不符。需要核对时走 [run-preflight.md](run-preflight.md)。
3. 产品定义、产线身份的修改在云后台，不在本页范围。
