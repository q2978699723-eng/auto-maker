# dsh-agent-builder

[English](./README.en.md) | 中文

把一句业务需求，按 **38 项 agent 产品定义** 问成一份可验收的 SPEC，再据此生成并安装 **DeepSeek Harness (DSH)** 的 agent preset。

面向产品经理：不用懂 Cordis 插件、不用懂 YAML，回答业务问题即可。面向工程师：产物是可审查的 preset 组合包 + 规范化工具代码。

## 它解决什么

DSH 里的「agent」不是一个提示词，而是若干插件行的组合：人设、工具、边界、记忆、知识、流程、异常、验收各自落到真实配置。难点不在写 YAML，而在**把产品定义说清楚**：

- 替谁办事？解决哪一类问题？明确不做什么？
- 一次任务怎么开始、怎么结束、失败怎么交代？
- 能自己执行什么？什么必须人工点头？什么话绝对不能说？
- 每个工具何时调用、入参返回、失败语义、有无副作用？
- 记谁、记什么、绝不记什么、留多久、何时召回？
- 依据哪份文档回答？冲突谁优先？没有答案怎么办？

这个 skill 用 **38 项定义 + 四类证据分级 + 7 个必答决策组** 把这些问清，产出 `SPEC.md`，再翻译成 DSH 配置。

## 目录

```
skills/dsh-agent-builder/          可安装的 skill 本体
├── SKILL.md                       主流程（10 域 38 项、证据纪律）
└── references/
    ├── definition-38.md           38 项逐条：问法/典型答案/判定/落位
    ├── module-map.md              DSH 包名与配置字段（已核对 0.2.2-rc.5）
    ├── preset-format.md           产物格式、自定义工具写法、安装验证
    └── spec-template.md           SPEC.md 模板

examples/aftersales/               完整示例：电商售后 agent
├── SPEC.md                        38 项已填写的产品定义
├── cordis.patch.yml               preset 声明（人设/工具/记忆/知识）
├── index.js                       三个业务工具（含核验与结构化错误码）
├── AGENTS.example.md              长期约束 + 售后政策（复制到工作区根）
└── package.json
```

## 安装

### 方式一：一条命令（推荐）

```bash
pip install "git+https://github.com/q2978699723-eng/auto-maker.git"
auto-maker install
```

`auto-maker` 会自动检测本机的 agent 目录并装到对应位置：

| agent | 技能目录 |
|---|---|
| DeepSeek Harness | `~/.dsh/skills/` |
| WorkBuddy | `~/.workbuddy/skills/` |
| Codex | `~/.codex/skills/` |
| Claude Code | `~/.claude/skills/` |

常用参数：

```bash
auto-maker list                      # 看检测到哪些 agent、装了没有
auto-maker install --target workbuddy # 只装 WorkBuddy
auto-maker install --target all       # 全部装上
auto-maker install --force            # 覆盖已安装
auto-maker install --path /some/skills # 手动指定目录
auto-maker uninstall --target workbuddy
auto-maker doctor                     # 校验打包内容与已装副本
```

不想全局安装时：

```bash
pipx run --spec "git+https://github.com/q2978699723-eng/auto-maker.git" auto-maker install
# 或
uvx --from "git+https://github.com/q2978699723-eng/auto-maker.git" auto-maker install
```

### 方式二：手动复制

```bash
git clone https://github.com/q2978699723-eng/auto-maker.git
cp -R auto-maker/skills/dsh-agent-builder ~/.dsh/skills/       # DeepSeek Harness
cp -R auto-maker/skills/dsh-agent-builder ~/.workbuddy/skills/ # WorkBuddy
```

> **为什么装错目录会「看不见」**：每个 agent 只扫描自己的技能根目录。装进 `~/.dsh/skills` 只有 DeepSeek Harness 能看到；WorkBuddy 只读 `~/.workbuddy/skills`。两个产品的 skill 格式相同（`SKILL.md` + YAML frontmatter），差别只在目录。


### 1. 装 skill

```sh
mkdir -p ~/.dsh/skills
cp -R skills/dsh-agent-builder ~/.dsh/skills/
```

DSH 会自动发现 `~/.dsh/skills/` 下的 skill（用户级，所有会话可见）。也可以放到工作区 `.dsh/skills/`，优先级更高。

### 2. 试跑示例 agent

```sh
# 复制政策与约束到工作区根（agent 每轮都会读）
cp examples/aftersales/AGENTS.example.md ./AGENTS.md

# 建记忆目录
mkdir -p ~/.dsh/agent-memory

# 安装 preset（绝对路径）
# 在 DSH 会话里让 agent 调用：
#   plugin_manager install_bundle { target: "<repo>/examples/aftersales" }
```

安装后新建会话，preset 选择器里应出现 **售后助手 v2**。

## 用法

对 agent 说：

> 我要做一个 AI 客服，帮我解决电商中的售后问题

skill 会：
1. 复述并拆解需求
2. 按 10 个域逐一访谈（每域 3–6 个问题，带推荐值与典型答案）
3. 每域结束复述定稿，回答写进 `SPEC.md`
4. 自检适配性（强一致实时数据 / 不可撤回承诺 / 其实只要知识问答）
5. 生成 `package.json` + `cordis.patch.yml` + `index.js`
6. 安装并验收，输出「已证明 / 未证明 / 阻断项」

## 三条来自实测的硬约束

1. **profile 安装的插件不能 `import '@deepseek-ai/dsh-tools'`** —— 该包只在 DSH 安装目录，profile 的 `node_modules` 解析不到，用 `defineTool` 会 `ERR_MODULE_NOT_FOUND`。必须直接传普通对象给 `ctx.tools.register()`。
2. **`parameters` 是标准 JSON Schema** —— `type: 'object'` + `properties` + `required` 数组，不是属性简写。
3. **`output.schema` 与 `output.render` 都是必填**。

## 已知边界

- **preset 只能由 Web/Desktop 组合**：`dsh headless` 与 `dsh acp` 明确不挂 preset 名册（源码注释「This bundle composes no preset roster」）。所以 CLI 无法端到端验证 preset 会话，最终 UAT 必须在新 Web 会话里做。
- 工具与记忆可以单独用临时全局挂载在 headless 里验证。
- 示例使用 mock 数据；接真实系统时替换 `index.js` 里的 `ORDERS`/`REFUNDS` 与 `execute` 中的请求。

## 证据说明

本项目区分四类证据，交付时必须分开陈述：

| 标记 | 能得出的结论 | 不能扩大成 |
|---|---|---|
| 源码核对 | DSH 里有该字段/机制 | 这个 agent 已实测可用 |
| 本次体验 | 这次操作出现了该结果 | 所有模型/环境都成立 |
| 工程推断 | 有依据的待验证解释 | 已定位且已修复 |
| 待决定 | 需产品经理选择 | 默认已开启 |

## 许可

MIT，见 [LICENSE](./LICENSE)。发布前请把 `<YOUR NAME>` 换成你的名字或组织名。

第三方依赖与商标归各自所有者：DeepSeek Harness、`@modelcontextprotocol/server-memory`。
