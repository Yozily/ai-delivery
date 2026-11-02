# 开测前检查

问题举例：「能不能测？」「帮我启动测试。」

你不能启动、停止、终止或重试测试；即使条件全部满足，也请用户在界面操作。你能做的是按下表检查，再给出结论。

## 检查清单

| 检查项 | 怎么查 | 不满足时 |
|---|---|---|
| 服务就绪 | 就绪接口 `status: ready`（[production.md](production.md)） | 阻塞 |
| 产线身份 | 身份状态 `active`（[production.md](production.md)） | 阻塞 |
| 工单有效 | 生产上下文 `orderValid`（[production.md](production.md)） | 阻塞 |
| 工单型号与要测的项目相符 | 没有字段关联型号与项目。能查到的是本机实际在用的项目：最近记录或活跃执行的 `projectId` | 把工单型号和实际在用的项目一起告诉用户，请用户确认是否相符；不要自行判定相符或不符 |
| 产品定义与生产配置已绑定 | 生产上下文中两者字段非空（[production.md](production.md)） | 很可能阻塞，标为推测 |
| 项目有可用部署 | 单个部署 `status: active`、`releaseAvailability: verified`（[flow.md](flow.md)） | 阻塞。历史部署通常也满足，所以这一项只能排除「没有部署」 |
| 当前会话状态 | 按 [run.md](run.md)「找本机在用的执行」查活跃执行 | `Waiting` 是常驻会话在等触发，属正常；其工作台 `executionFailures` 有失败时按 [run.md](run.md)「执行失败码」转述；未查过的部署写「未知」 |
| 上一次运行结果 | 最近一条测试记录（[record.md](record.md)） | 失败时提醒用户先处理 |
| 设备在线 | 当前无接口。单个部署的 `appliedLocalBindings.devicePortMappings` 列出绑定的设备端口，可提示用户逐一检查；两个设备映射到同一个端口时特别指出 | 写「未知」，请用户在界面确认 |
| 云后台可达 | 生产上下文 `cloudSync.lastError` | 不阻塞启动，但记录传不上去 |

## 结论口径

结论只用三种之一，并附上清单：

- 「满足已查条件，可以在界面启动」
- 「有阻塞项，先处理」
- 「有未知项，请在界面确认」

程度：前提检查部分可做；启动不开放。
