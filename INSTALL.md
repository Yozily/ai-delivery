# 安装

## 最省事的方式：让 AI 自己装

把下面这段发给你的 AI（Claude Code、Codex 或别的 agent），把 `<产品线>` 换成 [INDEX.md](INDEX.md) 里的产品线名：

```
拉取 https://github.com/Yozily/ai-delivery 的 <产品线> 目录，
安装其中 skills/ 下的全部技能到你的技能目录，
然后阅读该目录下的 README、docs 与 references，告诉我你能用它做什么、有哪些操作是不允许的。
```

**产品不是最新版本时**：把目录换成 `<产品线>/releases/<版本号>`，安装与你的产品版本对应的快照。产品接口会随版本变化，装错版本时 AI 会按不匹配的接口调用，看起来"调用成功"，结果却是错的。适用的产品版本见各目录的 `MANIFEST.json`。

产品目录的 `skills/` 下可能有多个技能（套件）：`<产品线>-shared` 是共享底座，其余是各业务域的技能，全部安装。

## 三种宿主

| 宿主 | 技能目录 | 说明 |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/`（个人）或 `<项目>/.claude/skills/`（项目内） | 把产品目录下的 `skills/<name>/` 整个复制进去 |
| Codex | `~/.agents/skills/` 或项目内 `.agents/skills/` | 同上 |
| Cherry Studio | 【设置】→【技能】→ 从文件夹或 ZIP 安装 | 选择产品目录下的 `skills/<name>/`；再在 Agent 的【技能】中启用 |
| 通用 agent | 无固定目录 | 把 `skills/<name>/SKILL.md` 与 `references/` 一起提供给 agent，或直接把内容贴进对话 |

## 手动安装（三选一）

**方式一：整目录复制.** 见上表。

**方式二：只读不改.** 把 `skills/<name>/` 放到任意位置，在对话里让 AI 先读 `SKILL.md`。SKILL.md 是自包含的，里面的相对链接指向同目录的 `references/`。

**方式三：不用技能.** 若该版本提供 `prompts/`，可直接复制其中的提示词，不需要 agent 支持技能机制。是否提供以该目录的 `MANIFEST.json` 为准。

## 需要访问产品服务时

部分技能需要读取你本地运行的产品服务。产品目录的 `docs/` 会说明需要什么工具（例如只读 HTTP 请求）和服务地址怎么获取。按说明配置后再提问。

## 只有 MCP 没有技能时

`mcp/<name>/contract.md` 是工具合同（工具名、输入、输出、错误码）。按合同里的传输方式（stdio 或 Streamable HTTP）在你的宿主里配置 MCP server；远程地址需要认证。**工具合同与技能必须同版本**，混用会出现工具名不一致。

## 安装后确认

对你的 AI 说：

```
把你刚装的 <产品线> 能力的清单列出来，标明哪些操作是只读的、哪些需要我确认。
```

如果它列不出，或列出的工具名和该目录 `MANIFEST.json` 的 `assets` 对不上，说明没装好。

## 卸载

删除对应的 `skills/<name>/` 目录即可，不留系统状态。
