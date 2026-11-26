# dsh-agent-builder

[English](./README.en.md) | 中文

**为具体业务场景配置并上线一个 agent。**

把业务需求逐项问清（或直接接收你已经写好的定义），据此产出人设、按需知识、前置判断、意图识别、业务工具、权限与审批闸门、委派与压缩的完整配置，打成可安装的 preset 组合包，装进运行环境后按用例验收。

面向产品经理：不用懂插件、不用懂 YAML，回答业务问题即可。
面向工程师：产物是可审查的组合包 + 规范化工具代码 + 可复跑的验收记录。

## 它解决什么

在 DSH 里「做一个 agent」不是改一个配置文件，而是组合若干插件行。真正的难点有三层：

1. **把业务说清楚**：替谁办事、不做什么、什么必须人工、失败怎么说、怎么证明做对了。
2. **把定义翻译成模块**：哪些用 persona，哪些用按需 skill，哪些必须写成 `agent/pre-step` / `tools/pre-execute` 闸门。
3. **承认提示词不是强制手段**：只写在提示词里的规则是「大概率照做」，不是「一定不发生」。所以关键约束要落到代码闸门或入口拦截。

这个 skill 用 **48 项定义（十个业务域 + 工程闸门域）+ 四类证据分级 + 7 个必答决策组** 把这些问清，产出 `SPEC.md`，再翻译成可安装的配置。

## 两种模式

| 你的处境 | 走哪条路 |
|---|---|
| 只有一句业务描述 | **访谈模式**：一次一域问清，边问边写 `SPEC.md` |
| 已有定义 / 一份 SPEC / 「别问了直接做」 | **执行模式**：缺口扫描 → 只问阻塞项 → 直接构建、安装、验收 |

## 目录

```
skills/dsh-agent-builder/          可安装的 skill 本体
├── SKILL.md                       主流程（双模式、48 项、模块装配、工程规范）
└── references/
    ├── definition-48.md           48 项逐条：问法/典型答案/判定/落位
    ├── engineering-execution.md   包结构、工具模板、三种闸门、12 条验收用例、DoD
    ├── module-map.md              包名与配置字段（已核对 0.2.2-rc.5）
    ├── preset-format.md           产物格式、自定义工具写法、安装验证
    └── spec-template.md           SPEC.md 模板

examples/aftersales/               完整示例：电商售后 agent
├── SPEC.md                        48 项已填写的产品定义
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
auto-maker list                       # 看检测到哪些 agent、装了没有
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

### 试跑示例 agent

```sh
# 复制政策与约束到工作区根（agent 每轮都会读）
cp examples/aftersales/AGENTS.example.md ./AGENTS.md

# 建记忆目录
mkdir -p ~/.dsh/agent-memory

# 安装 preset（绝对路径），在会话里让 agent 调用：
#   plugin_manager install_bundle { target: "<repo>/examples/aftersales" }
```

安装后新建会话，preset 选择器里应出现 **售后助手 v2**。

## 用法

对 agent 说：

> 我要做一个 AI 客服，帮我解决电商中的售后问题

skill 会：

1. 复述并拆解需求
2. 按 10 个业务域逐一访谈（每域 3–6 个问题，带推荐值与典型答案）
3. 每域结束复述定稿，答案即时写进 `SPEC.md`
4. 自检适配性（强一致实时数据 / 不可撤回承诺 / 其实只要知识问答）
5. 补齐工程闸门域（规则落点、冲突裁决、失败方向、权限粒度、委派、压缩、循环上限、大结果）
6. 生成 `package.json` + `cordis.patch.yml` + `index.js`
7. 安装并验收，输出「已证明 / 未证明 / 阻断项」

## 三条硬约束

1. **profile 安装的插件不能 `import '@deepseek-ai/dsh-tools'`** —— 该包只在安装目录里，profile 的 `node_modules` 解析不到，用 `defineTool` 会 `ERR_MODULE_NOT_FOUND`。必须直接传普通对象给 `ctx.tools.register()`。
2. **`parameters` 是标准 JSON Schema** —— `type: 'object'` + `properties` + `required` 数组，不是属性简写。
3. **`output.schema` 与 `output.render` 都是必填**。

## 已知边界

- **preset 只能由 Web/Desktop 组合**：`dsh headless` 与 `dsh acp` 明确不挂 preset 名册。所以 CLI 无法端到端验证 preset 会话，最终 UAT 必须在新 Web 会话里做。
- **`agent/pre-step` 只能否决或改写消息**，不能直接发一条固定回复；「命中即转人工」若要零模型，得放到入口层。
- 示例使用 mock 数据；接真实系统时替换 `index.js` 里的 `ORDERS`/`REFUNDS` 与 `execute` 中的请求。

## 证据说明

交付时必须分开陈述「已证明」与「未证明」：

| 标记 | 能得出的结论 | 不能扩大成 |
|---|---|---|
| 源码核对 | 运行环境里有该字段/机制 | 这个 agent 已实测可用 |
| 本次体验 | 这次操作出现了该结果 | 所有模型/环境都成立 |
| 工程推断 | 有依据的待验证解释 | 已定位且已修复 |
| 待决定 | 需业务方选择 | 默认已开启 |

**「装上了」不等于「验收通过」。**

## 许可

MIT，见 [LICENSE](./LICENSE)。发布前请把 `<YOUR NAME>` 换成你的名字或组织名。

第三方依赖与商标归各自所有者：DeepSeek Harness、`@modelcontextprotocol/server-memory`。
