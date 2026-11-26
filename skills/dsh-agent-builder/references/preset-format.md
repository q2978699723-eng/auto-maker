# 产物格式与安装

## 目录结构

```
<workspace>/<agent-id>-preset/
├── package.json
├── cordis.patch.yml
└── index.js          # 仅当需要自定义工具
```

`<agent-id>` 用英文小写与连字符，和 preset 的 `id` 一致。

## package.json

纯组合包（只挂内置插件，不写代码）：

```json
{
  "name": "@local/dsh-agent-<agent-id>",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } }
}
```

含自定义工具时加 `"exports": { ".": "./index.js" }`。

## cordis.patch.yml（核心）

```yaml
- insert:
    - id: preset-<agent-id>
      name: '@deepseek-ai/dsh-agent-preset'
      config:
        id: <agent-id>
        name: 售后助手
        description: 处理电商售后咨询，查询订单与政策，超阈值转人工。
        order: 20
        plugins:
          - id: persona
            name: '@deepseek-ai/dsh-persona'
            config:
              prefix: |
                你是 <品牌> 的售后客服助手。……
                ## 可以
                - ……
                ## 不可以
                - ……
                ## 转人工
                - ……
          - id: agent-instructions
            name: '@deepseek-ai/dsh-agent-instructions'
            config:
              maxBytes: 32768
          - id: tool-ask-user
            name: '@deepseek-ai/dsh-tool-ask-user'
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

要点：
- 行 `id` 在整棵树里唯一；`preset-<id>` 是约定。
- `config.plugins` 里的顺序就是加载顺序。
- 需要分组隔离服务时用 `name: cordis:group` + `group: true` + `isolate`，一般场景不需要。
- `!!js` 表达式只在 `config` 或 `disabled` 里用。

## 自定义工具（index.js）

只在业务动作没有现成接口时才写。

> **重要：profile 里的插件无法 `import '@deepseek-ai/dsh-tools'`。** 该包只在运行时安装目录里，profile 的 `node_modules` 解析不到，用 `defineTool` 会报 `ERR_MODULE_NOT_FOUND`。**不要 import 任何 `@deepseek-ai/*` 包**，直接传普通对象给 `ctx.tools.register()`——已在本机实测通过。

```js
export const name = 'agent-tools'
export const inject = ['tools']

export function apply(ctx) {
  ctx.tools.register({
    name: 'lookup_order',
    description: '按订单号查询订单状态与物流节点。只读，不修改任何数据。',
    parameters: {
      type: 'object',
      properties: {
        orderId: { type: 'string', description: '订单号，形如 SO-2026-000123' },
      },
      required: ['orderId'],
      additionalProperties: false,
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          status: { type: 'string' },
          carrier: { type: 'string' },
          tracking: { type: 'string' },
          updatedAt: { type: 'string' },
        },
      },
      render: (_args, value) => [{ type: 'text', text: JSON.stringify(value) }],
    },
    async execute({ orderId }) {
      const res = await fetch(`https://api.example.com/orders/${encodeURIComponent(orderId)}`)
      if (!res.ok) throw new Error(`订单查询失败: HTTP ${res.status}`)
      const data = await res.json()
      return {
        status: String(data.status ?? ''),
        carrier: String(data.carrier ?? ''),
        tracking: String(data.tracking ?? ''),
        updatedAt: String(data.updatedAt ?? ''),
      }
    },
  })
}
```

要点：
- `parameters` 是**标准 JSON Schema**（`type: 'object'` + `properties` + `required` 数组），不是 `defineTool` 的属性简写。
- `output.schema` 与 `output.render` 都是必填；`render` 返回内容块数组，最常用 `{ type: 'text', text }`。
- `execute` 的返回值必须符合 `output.schema`。
- 只读工具不要顺手写副作用；写操作要单独一个工具，命名里体现（如 `create_ticket`）。

挂载时用包内的 index.js：

```yaml
- id: agent-tools
  name: './index.js'
  inject: ['tools']
```

`name` 以 `.` 开头即按相对 `cordis.patch.yml` 的路径解析。含自定义工具的包，`package.json` 里加 `"exports": { ".": "./index.js" }`。

## 安装

用 `plugin_manager` 的 `install_bundle`，`target` 是这个目录的**绝对路径**：

```
install_bundle { target: "<workspace>/<agent-id>-preset" }
```

读返回：
- `application: applied` → 已生效
- `warnings` 非空 → 逐条修
- `application: failed` → 看 `diagnostic`，修同一个目录重装，不要新建第二个目录

## 验证

1. 新会话 → preset 选择器里应出现 `name` 指定的名字。
2. 选它，问一个真实业务问题，确认：
   - 工具被调用（而不是凭空回答）
   - 越界问题被正确拒答或转人工
   - 记忆写入后，**另一个新会话**能召回
3. 已有会话不会自动切换 preset。

## 更新

改同一个目录的文件，重新 `install_bundle` 同一路径。不要改 profile 的 `package.json` 或 `cordis.patch.yml`——安装器负责这些。
