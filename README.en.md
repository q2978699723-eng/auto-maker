# dsh-agent-builder

[中文](./README.md) | English

**Configure and ship an agent for a concrete business scenario.**

It settles the business requirements item by item (or takes the definition you already wrote), then produces the full configuration — persona, on-demand knowledge, pre-step checks, intent routing, business tools, permission and approval gates, delegation and compaction — packages it into an installable preset bundle, installs it, and verifies it against acceptance cases.

For product managers: no plugin knowledge, no YAML — just answer business questions.
For engineers: the output is a reviewable bundle, normalized tool code, and a re-runnable acceptance record.

## What it solves

An "agent" here is not a config file; it is a composition of plugin rows. The hard part is threefold:

1. **Make the business explicit**: who it serves, what it must not do, what requires a human, how failures are reported, how you prove it works.
2. **Translate the definition into modules**: what belongs in persona, what belongs in on-demand skills, what must become an `agent/pre-step` or `tools/pre-execute` gate.
3. **Accept that a prompt is not an enforcement mechanism**: a rule written only in the prompt is "usually followed", not "cannot happen". Critical constraints belong in code gates or entry-layer interception.

This skill settles all of that with **48 definition items (ten business domains + an engineering-gate domain) + four evidence levels + 7 mandatory decision groups**, produces `SPEC.md`, then translates it into installable configuration.

## Two modes

| Your situation | Which path |
|---|---|
| Only a one-line business description | **Interview mode**: settle one domain at a time, writing `SPEC.md` as you go |
| A definition / a SPEC / "stop asking, just build it" | **Execution mode**: gap scan → ask only blockers → build, install, verify |

## Layout

```
skills/dsh-agent-builder/          the installable skill
├── SKILL.md                       main flow (dual mode, 48 items, module assembly, engineering rules)
└── references/
    ├── definition-48.md           48 items: question / typical answer / criterion / mapping
    ├── engineering-execution.md   bundle layout, tool template, three gates, 12 acceptance cases, DoD
    ├── module-map.md              package names and config fields (verified 0.2.2-rc.5)
    ├── preset-format.md           output format, custom tool rules, install & verify
    └── spec-template.md           SPEC.md template

examples/aftersales/               complete example: e-commerce after-sales agent
├── SPEC.md                        all 48 items filled in
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

### Try the example agent

```sh
cp examples/aftersales/AGENTS.example.md ./AGENTS.md   # agent reads it every turn
mkdir -p ~/.dsh/agent-memory                            # memory file location
```

Then install the preset from a session:

```
plugin_manager install_bundle { target: "<repo>/examples/aftersales" }
```

Open a new session; **售后助手 v2** should appear in the preset picker.

## Usage

Tell the agent:

> I want an AI customer-service agent for e-commerce after-sales.

The skill will:

1. restate and decompose the requirement
2. interview you across 10 business domains (3–6 questions each, with defaults and typical answers)
3. restate each domain's conclusion, writing answers into `SPEC.md` immediately
4. run a fitness check (strongly consistent real-time data / irrevocable commitments / actually just knowledge Q&A)
5. settle the engineering-gate domain (rule placement, conflict precedence, failure direction, permission granularity, delegation, compaction, loop caps, large results)
6. generate `package.json` + `cordis.patch.yml` + `index.js`
7. install and verify, reporting **Proven / Not proven / Blockers**

## Three hard constraints

1. **A profile-installed plugin cannot `import '@deepseek-ai/dsh-tools'`** — that package lives in the installation directory, not the profile's `node_modules`; `defineTool` fails with `ERR_MODULE_NOT_FOUND`. Pass a plain object to `ctx.tools.register()` instead.
2. **`parameters` is standard JSON Schema** — `type: 'object'` + `properties` + a `required` array.
3. **`output.schema` and `output.render` are both mandatory.**

## Known limits

- **Presets only compose in Web/Desktop.** `dsh headless` and `dsh acp` mount no preset roster, so CLI cannot exercise a preset-selected session. Final UAT must happen in a new Web session.
- **`agent/pre-step` can only reject or rewrite messages** — it cannot send a fixed reply. Zero-model "route straight to human" must live at the entry layer.
- The example uses mock data; replace `ORDERS`/`REFUNDS` and the `execute` bodies to hit a real system.

## Evidence discipline

Deliverables must keep "proven" and "not proven" apart:

| Tag | What it establishes | What it must not be stretched into |
|---|---|---|
| source-verified | the runtime has this field/mechanism | this agent is tested |
| observed | this run produced this result | holds for every model/environment |
| engineering inference | a grounded but unverified explanation | located and fixed |
| to-be-decided | a choice only the business owner can make | enabled by default |

**"Installed" is not "accepted".**

## License

MIT — see [LICENSE](./LICENSE). Replace `<YOUR NAME>` before publishing.

Third-party dependencies and trademarks belong to their owners: DeepSeek Harness, `@modelcontextprotocol/server-memory`.
