# dsh-agent-builder

Turn a one-line business requirement into an **acceptance-ready agent product spec** (38 items), then generate and install a **DeepSeek Harness (DSH)** agent preset from it.

For product managers: no Cordis plugins, no YAML — just answer business questions.
For engineers: the output is a reviewable preset bundle plus normalized tool code.

[中文](./README.md) | English

## What it solves

An "agent" in DSH is not a prompt; it is a composition of plugin rows: persona, tools, boundaries, memory, knowledge, task flow, failure handling, and acceptance criteria. The hard part is not writing YAML — it is **making the product definition explicit**:

- Who is it for? Which class of problem? What does it explicitly *not* do?
- How does a task start, finish, and fail?
- What may it execute on its own? What needs human approval? What must it never say?
- For each tool: when to call, inputs, outputs, failure semantics, side effects?
- What to remember, what to never remember, for how long, when to recall?
- Which document is authoritative? What wins on conflict? What if there is no answer?

This skill uses **38 definition items + four evidence levels + 7 mandatory decision groups** to settle those, produce `SPEC.md`, then translate it into DSH configuration.

## Layout

```
skills/dsh-agent-builder/          the installable skill
├── SKILL.md                       main flow (10 domains / 38 items / evidence rules)
└── references/
    ├── definition-38.md           38 items: question / typical answer / criterion / mapping
    ├── module-map.md              DSH package names and config fields (verified 0.2.2-rc.5)
    ├── preset-format.md           output format, custom tool rules, install & verify
    └── spec-template.md           SPEC.md template

examples/aftersales/               complete example: e-commerce after-sales agent
├── SPEC.md                        all 38 items filled in
├── cordis.patch.yml               preset declaration (persona/tools/memory/knowledge)
├── index.js                       three business tools (verification + structured error codes)
├── AGENTS.example.md              long-lived constraints + after-sales policy
└── package.json
```

## Install

### Option 1: one command (recommended)

```bash
pip install "git+https://github.com/q2978699723-eng/auto-maker.git"
auto-maker install
```

`auto-maker` detects every agent home on this machine and installs into each one:

| Agent | Skill directory |
|---|---|
| DeepSeek Harness | `~/.dsh/skills/` |
| WorkBuddy | `~/.workbuddy/skills/` |
| Codex | `~/.codex/skills/` |
| Claude Code | `~/.claude/skills/` |

Common flags:

```bash
auto-maker list                       # what is detected and installed
auto-maker install --target workbuddy # only WorkBuddy
auto-maker install --target all       # every known agent
auto-maker install --force            # overwrite
auto-maker install --path /some/skills
auto-maker uninstall --target workbuddy
auto-maker doctor                     # validate the packaged copy
```

No global install needed:

```bash
pipx run --spec "git+https://github.com/q2978699723-eng/auto-maker.git" auto-maker install
# or
uvx --from "git+https://github.com/q2978699723-eng/auto-maker.git" auto-maker install
```

### Option 2: copy by hand

```bash
git clone https://github.com/q2978699723-eng/auto-maker.git
cp -R auto-maker/skills/dsh-agent-builder ~/.dsh/skills/       # DeepSeek Harness
cp -R auto-maker/skills/dsh-agent-builder ~/.workbuddy/skills/ # WorkBuddy
```

> **Why the wrong directory makes it invisible**: each agent scans only its own skill root. A copy in `~/.dsh/skills` is visible to DeepSeek Harness only; WorkBuddy reads `~/.workbuddy/skills`. The formats are identical (`SKILL.md` + YAML frontmatter) — only the location differs.


### 1. Install the skill

```sh
mkdir -p ~/.dsh/skills
cp -R skills/dsh-agent-builder ~/.dsh/skills/
```

DSH discovers `~/.dsh/skills/` automatically (user scope, all sessions). A workspace-level `.dsh/skills/` also works and takes precedence.

### 2. Try the example agent

```sh
cp examples/aftersales/AGENTS.example.md ./AGENTS.md   # agent reads it every turn
mkdir -p ~/.dsh/agent-memory                            # memory file location
```

Then install the preset from a DSH session:

```
plugin_manager install_bundle { target: "<repo>/examples/aftersales" }
```

Open a new session; **售后助手 v2** should appear in the preset picker.

## Usage

Tell the agent:

> I want an AI customer-service agent for e-commerce after-sales.

The skill will:
1. restate and decompose the requirement
2. interview you across 10 domains (3–6 questions each, with defaults and typical answers)
3. restate each domain's conclusion, writing answers into `SPEC.md`
4. run a fitness check (strongly consistent real-time data / irrevocable commitments / actually just knowledge Q&A)
5. generate `package.json` + `cordis.patch.yml` + `index.js`
6. install and verify, reporting **Proven / Not proven / Blockers**

## Three hard-won constraints

1. **A profile-installed plugin cannot `import '@deepseek-ai/dsh-tools'`** — that package lives in the DSH installation, not the profile's `node_modules`; `defineTool` fails with `ERR_MODULE_NOT_FOUND`. Pass a plain object to `ctx.tools.register()` instead.
2. **`parameters` is standard JSON Schema** — `type: 'object'` + `properties` + a `required` array.
3. **`output.schema` and `output.render` are both mandatory.**

## Known limits

- **Presets only compose in Web/Desktop.** `dsh headless` and `dsh acp` explicitly mount no preset roster (source comment: "This bundle composes no preset roster"), so CLI cannot exercise a preset-selected session. Final UAT must happen in a new Web session.
- Tools and memory *can* be verified by temporarily mounting them globally in headless.
- The example uses mock data; replace `ORDERS`/`REFUNDS` and the `execute` bodies to hit a real system.

## Evidence discipline

Four evidence levels; deliverables must keep them apart:

| Tag | What it establishes | What it must not be stretched into |
|---|---|---|
| source-verified | DSH has this field/mechanism | this agent is tested |
| observed | this run produced this result | holds for every model/environment |
| engineering inference | a grounded but unverified explanation | located and fixed |
| to-be-decided | a product choice only the PM can make | enabled by default |

## License

MIT — see [LICENSE](./LICENSE). Replace `<YOUR NAME>` before publishing.

Third-party dependencies and trademarks belong to their owners: DeepSeek Harness, `@modelcontextprotocol/server-memory`.
