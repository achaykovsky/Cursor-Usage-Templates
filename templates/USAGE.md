# Cursor Config — Usage Hub

**Location:** `.cursor/USAGE.md` (this file after sync). **Start here** in every project — route by intent; do not load full catalogs into chat.

## Initialize

| Scenario | Command |
|----------|---------|
| **Templates → global** `~/.cursor/` | `python templates/commands/sync-cursor.py --mode TemplatesToGlobal` |
| **Global → project** | `python <path>/templates/commands/sync-cursor.py --mode FromGlobal --project-root <project>` |
| Refresh project from **templates** | `python templates/commands/sync-cursor.py` |
| Project `.cursor/` → global | `python templates/commands/sync-cursor.py --mode ToGlobal` |

| Doc | When to open |
|-----|----------------|
| [agents/AGENTS_USAGE.md](agents/AGENTS_USAGE.md) | `@agent(NAME)` invocation and workflows |
| [skills/SKILLS.md](skills/SKILLS.md) | Pick a workflow skill by task keywords |
| [rules/RULES.md](rules/RULES.md) | Which rules apply to which files |
| [hooks/HOOKS_USAGE.md](hooks/HOOKS_USAGE.md) | Hooks: blocks, gates, logs |
| [prompts/](prompts/) | Paste prompts when routing is unclear |

---

## Four layers (pick one primary per message)

| Layer | You choose? | Purpose | Token cost |
|-------|-------------|---------|------------|
| **Rules** | No (auto by glob) | Standards while editing matching files | Low — only active globs load |
| **Skills** | Implicit (agent reads `SKILL.md` when relevant) | Step-by-step workflows | Medium — one skill per task |
| **Agents** | Yes — `@agent(NAME)` | Role, tone, domain ownership | Medium — one agent per turn |
| **Hooks** | No (lifecycle scripts) | Safety, format, logging, gates | Zero in chat — side effects only |

**Precedence:** security/safety → scoped **rules** → **skills** → **agents** → examples. See [agents/AGENTS.md](agents/AGENTS.md#policy-precedence).

---

## Routing decision tree

```
What do you need?
├─ Automatic standards while editing → rules (no action; see rules/RULES.md)
├─ Step-by-step procedure → skill (name the task; agent picks SKILL.md)
├─ Specialist persona / review tone → @agent(NAME)
├─ Blocked command or redacted file → hooks/HOOKS_USAGE.md
└─ Unsure → paste prompts/plan-cursor-session-map.md
```

### Intent → first hop

| Intent | Start with | Escalate to |
|--------|------------|-------------|
| New to repo / where is X | `explain-codebase-structure` | `@agent(PM)` |
| Feature / requirements | `@agent(PM)` or `design-feature-from-requirements` | `BACKEND_*`, `FE_*` |
| Frontend (multi-step) | `orchestrate-frontend-delivery` | `FE_*` per step |
| API implement / extend | `implement-or-extend-api-surface` | `BACKEND_PYTHON` / `BACKEND_GO` |
| API breaking / version | `check-api-backward-compatibility` | `handle-breaking-change` |
| Bug / failure | `reproduce-and-document-failure` → `fix-bug-systematically` | `@agent(INCIDENT)` if prod |
| PR / code review | `review-pull-request` | `@agent(REVIEWER)`; FE: `review-frontend-code` |
| Security | `@agent(SECURITY)` or `security-scan-changes` | `sensitive-data-handling` |
| Tests | `@agent(TESTER)` or `add-tests-for-change` | FE: `add-frontend-tests-for-change` |
| Performance | `@agent(PERFORMANCE)` or `investigate-performance-issue` | FE: `optimize-core-web-vitals` |
| Release / deploy | `validate-pre-deploy` | `prepare-release`, `@agent(DEVOPS)` |
| Docs / ADR | `@agent(DOCS)` | `keep-docs-in-sync-with-code` |
| Architecture | `@agent(ARCHITECT)` | `evaluate-architecture-tradeoffs` |
| Infra / CI | `@agent(DEVOPS)` | devops-workflows skills |
| DB | `@agent(DATABASE_SQL)` / `DATABASE_NOSQL` | sql/nosql rules on edit |

**One agent per turn** unless sequencing. **Reference files** (`@path`), don't paste catalogs.

---

## Token-efficient prompting

1. **One intent per message** — plan → implement → test → review.
2. **Reference, don't paste** — `@file` or line ranges.
3. **Name the route** — `@agent(REVIEWER) review @src/auth.py`.
4. **Orchestrate multi-domain FE** — `orchestrate-frontend-delivery`, not eight skills.
5. **Planning prompts only when stuck** — [prompts/plan-cursor-session-map.md](prompts/plan-cursor-session-map.md).
6. **Hooks are automatic** — see [hooks/HOOKS_USAGE.md](hooks/HOOKS_USAGE.md) only when debugging.

Skill: `save-tokens-in-context` when context is large.

---

## Planning prompts

| Prompt | Use when |
|--------|----------|
| [plan-cursor-session-map.md](prompts/plan-cursor-session-map.md) | Full route for one task |
| [plan-cursor-agents-routing.md](prompts/plan-cursor-agents-routing.md) | `@agent` only |
| [plan-cursor-skills-routing.md](prompts/plan-cursor-skills-routing.md) | Skills only |
| [plan-cursor-model-routing.md](prompts/plan-cursor-model-routing.md) | Model tier + slug only |
| [plan-cursor-rules-audit.md](prompts/plan-cursor-rules-audit.md) | Rules for given files |
| [plan-cursor-hooks.md](prompts/plan-cursor-hooks.md) | Extend hooks |
| [plan-cursor-activity-logging.md](prompts/plan-cursor-activity-logging.md) | Activity logs |
| [plan-python-remediation-overview.md](prompts/plan-python-remediation-overview.md) | Python hooks/sync remediation (P0–P3) |

---

## Template repo maintenance

Source lives under `templates/` in **Cursor-Usage-Templates**. Edit there, then:

1. `python templates/commands/sync-cursor.py --mode TemplatesToGlobal` — update `~/.cursor/`
2. `python templates/commands/sync-cursor.py` — refresh this repo’s `.cursor/` (optional)
3. In other projects: `FromGlobal` to pull global into `project/.cursor/`

See `templates/README.md` in the Cursor-Usage-Templates repo.

## Note
Codex will review your results for double-check.