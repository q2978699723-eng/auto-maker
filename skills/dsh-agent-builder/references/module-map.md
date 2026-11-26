# 模块地图

只列本机运行时（0.2.2-rc.5）里真实存在的包。`Config` 列表示该行接受 `config` 映射。

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

本运行时 **没有**内置的「用户记忆」数据库，记忆靠这三条路，按需要选：

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

MCP 工具会以 `mcp__memory__<tool>` 出现在模型面前。上游服务需自行安装/常驻，运行时不管。

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
| 命令沙箱 | `@deepseek-ai/dsh-bash-sandbox`，与 `dsh-tool-bash` 配对 |
| 审批 | `@deepseek-ai/dsh-user-approval` + `@deepseek-ai/dsh-permission-presets`，敏感动作走人工确认 |
| 自动审查 | `@deepseek-ai/dsh-experimental-auto-review`：逐工具 LLM 授权审查（Auto 档位），**实验包** |
| 干跑 | `@deepseek-ai/dsh-plan-mode`：先只读探索、人工审阅后再执行 |
| 提示词约束 | 写在 persona 的 `prefix` 里：不承诺、不报价、不判定责任、涉资金转人工 |

**权限分层**：工具白名单是「模型看不到」，沙箱是「看得到但落不了地」，审批是「能落地但要人点」。三层不可互相替代。

## 工程闸门（域 11 对应）

| 包 | Config | 说明 |
|---|---|---|
| `@deepseek-ai/dsh-spill-policy` | yes | 大结果溢出：超预算的结果存文件、给模型路径 + 预览（P48） |
| `@deepseek-ai/dsh-spill-local` | yes | 溢出的本地存储实现（私有、按会话） |
| `@deepseek-ai/dsh-tool-call-timeout-policy` | no | 逐工具超时，超时返回 `TOOL_TIMEOUT`（P47） |
| `@deepseek-ai/dsh-repeat-tool-reminder` | yes | 重复调用提醒；**只提醒不阻断**，真上限要自己写（P47） |
| `@deepseek-ai/dsh-session-checkpoint-policy` | no | 模型请求与工具副作用前的持久化检查点 |

## 上下文与压缩

| 包 | Config | 说明 |
|---|---|---|
| `@deepseek-ai/dsh-compaction-basic` | yes | 按 token 水位触发的压缩策略 + LLM 摘要后端 |
| `@deepseek-ai/dsh-compaction-tool-result-pruner` | yes | 免模型的 head/middle/tail 裁剪，先于 LLM 压缩跑 |
| `@deepseek-ai/dsh-token-meter` | yes | 上下文压力测量（`contextPressure`） |

压缩是有顺序的流水线：先免模型裁剪，再 LLM 摘要。顺序错了会出现「压了但阈值仍超限」。

## 委派与编排

| 包 | Config | 说明 |
|---|---|---|
| `@deepseek-ai/dsh-subagent` | yes | 子 agent 注册与生命周期 |
| `@deepseek-ai/dsh-subagent-spawn-in-process` | yes | 全新上下文子 agent |
| `@deepseek-ai/dsh-subagent-fork-in-process` | yes | 继承父会话前缀的子 agent |
| `@deepseek-ai/dsh-tool-subagent` | yes | 模型可调用的委派工具 |
| `@deepseek-ai/dsh-tool-subagent-control` | yes | 子 agent 消息、打断、发现 |
| `@deepseek-ai/dsh-agent-team` | yes | 子 agent 树共享任务 DAG |
| `@deepseek-ai/dsh-tool-agent-team` | yes | 模型可调用的看板工具 |
| `@deepseek-ai/dsh-tool-workflow` | yes | JS 编排脚本，扇出多个子 agent |

委派是同时的隔离手段与权限手段：子 agent 有独立上下文、工具集、模型。**深度与并发都要设上限**（P44）。

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
