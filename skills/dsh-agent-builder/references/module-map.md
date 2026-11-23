# 模块地图

只列本机 DSH 0.2.2-rc.5 里真实存在的包。`Config` 列表示该行接受 `config` 映射。

## 人设

| 包 | Config | 说明 |
|---|---|---|
| `@deepseek-ai/dsh-persona` | yes | 该 preset 专属人设。字段：`prefix`（必填）、`suffix`、`complete`（true 时 prefix 成为完整 system prompt，压制其它所有段）、`includeRuntimeContext` |

`complete: true` 会连工具说明、环境信息一起压掉，只在做纯话术机器人时用；通用客服用默认 `false`。

## 常用工具（按业务挑，不要全挂）

| 包 | Config | 说明 |
|---|---|---|
| `@deepseek-ai/dsh-tool-web` | yes | `web_search` + `web_fetch`；对外客服一般不需要 |
| `@deepseek-ai/dsh-tool-ask-user` | yes | `ask_user_question`；需要向运营/用户澄清时挂 |
| `@deepseek-ai/dsh-tool-todo` | yes | `todo_write`；多步流程拆解 |
| `@deepseek-ai/dsh-tool-skill` | yes | 让 agent 按需加载 skill（配合知识库） |
| `@deepseek-ai/dsh-tool-session-query` | yes | 检索本工作区历史会话，做「上次说过什么」 |
| `@deepseek-ai/dsh-tool-fs` | yes | 读写文件；只有确实要落盘时才给 |
| `@deepseek-ai/dsh-tool-fs-search` | yes | glob / grep |
| `@deepseek-ai/dsh-tool-bash` | yes | 执行命令；**对外客服默认不给** |
| `@deepseek-ai/dsh-tool-subagent` | yes | 委派子 agent |
| `@deepseek-ai/dsh-tool-office` | yes | 处理 Word/Excel/PDF |
| `@deepseek-ai/dsh-tool-present` | yes | 交付文件 |

## 记忆

DSH **没有**内置的「用户记忆」数据库，记忆靠这三条路，按需要选：

| 方式 | 怎么接 | 适合 |
|---|---|---|
| MCP 记忆服务 | `@deepseek-ai/dsh-mcp-client` 接 Memorix / MCP Reference Memory / Engram | 跨会话的长期用户记忆、偏好、历史工单 |
| 会话检索 | `@deepseek-ai/dsh-tool-session-query` + `@deepseek-ai/dsh-session-query-sqlite` | 「这个客户上次聊到哪」，限定在同一工作区 |
| 工作区指令 | `@deepseek-ai/dsh-agent-instructions` 读 `AGENTS.md` | 固定事实：品牌、政策、话术、禁答清单 |

MCP 记忆的最小行：

```yaml
- id: memory
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: memory
    transport: stdio
    command: npx
    args: ['-y', '@modelcontextprotocol/server-memory@2026.7.4']
    env:
      MEMORY_FILE_PATH: !!js process.env.HOME + '/.dsh-memory.jsonl'
```

MCP 工具会以 `mcp__memory__<tool>` 出现在模型面前。上游服务需自行安装/常驻，DSH 不代管。

## 知识

| 方式 | 说明 |
|---|---|
| `AGENTS.md` | 放在工作区根目录，`dsh-agent-instructions` 自动加载（默认 64 KiB 每链） |
| skill 目录 | `<workspace>/.dsh/skills/<name>/SKILL.md`，配合 `dsh-tool-skill` 按需加载 |
| MCP 只读工具 | 商品库、政策库已有服务时最省事 |

## 边界

| 手段 | 做法 |
|---|---|
| 工具白名单 | preset 里只列该有的行——**没挂的工具模型根本调不到**，这是最强的一道 |
| 文件沙箱 | `@deepseek-ai/dsh-sandbox-policy` 的 `mode`：`read-only` / `workspace-write` |
| 审批 | `@deepseek-ai/dsh-user-approval` + `@deepseek-ai/dsh-permission-presets`，敏感动作走人工确认 |
| 提示词约束 | 写在 persona 的 `prefix` 里：不承诺、不报价、不判定责任、涉资金转人工 |

## 模型

`@deepseek-ai/dsh-agent-default-model`（profile 级，不是 preset 级）：

```yaml
- id: agent-default-model
  config:
    provider: our-free-model
    model: deepseek-v4.1-flash-free
    reasoningEffort: high
```

## 已装载率检查

不确定某包是否存在于当前版本时，直接查：

```sh
ls "$DSH_INSTALL_DIR/../" | grep dsh-tool
```

或读 `$DSH_INSTALL_DIR/README.md` 与各包 `package.json`。不要凭记忆写包名。
