---
name: route-task-to-model
description: Selects the best Cursor model tier and slug for a coding task using a trade-off matrix (frontier vs mid-tier vs lightweight). Refreshes tier picks from the web against the Cursor allowlist. Use when choosing a model, spawning Task subagents with model=, routing by cost/speed/reasoning, or updating model defaults.
---

# Route Task to Model

Pick a **model tier** first, then a **Cursor slug** from [models-catalog.json](models-catalog.json). Never recommend models outside `cursor_allowlist`.

## Model Selection Framework: Efficiency & Trade-offs

This framework dictates how to select an AI model for any given coding task based on the trade-offs between reasoning quality, speed, cost, and token efficiency.

### 1. Trade-off Matrix
Select your model class based on the core requirement of the specific task:

| Requirement | Best-Fit Model Class | Trade-off Profile |
| :--- | :--- | :--- |
| **Complex Logic / Architecture** | Frontier Reasoning Models | Highest quality; high cost/latency; lower token efficiency. |
| **General Development** | Mid-Tier Balanced Models | Optimal balance of speed, cost, and reasoning quality. |
| **Boilerplate / Simple Edits** | Lightweight "Mini" Models | Highest speed and token efficiency; lowest cost. |

### 2. Decision Criteria
Before executing a task, categorize it to balance your resources:

*   **Architectural & Structural Tasks:** Choose Frontier Reasoning Models. These are required when the task involves multi-file refactoring, deep dependency analysis, or designing new system components where logical consistency is critical.
*   **General Purpose Tasks:** Choose Mid-Tier Balanced Models. These are ideal for daily development, feature implementation, and API integration where the code is well-scoped and the logic is straightforward.
*   **Repetitive & Routine Tasks:** Choose Lightweight/Mini Models. These should be the default for boilerplate generation, unit test scaffolding, documentation, and routine logging instrumentation, as they prioritize performance, cost-effectiveness, and token efficiency over deep reasoning.

### 3. Workflow Discipline for Model Execution
To ensure the chosen model performs optimally regardless of the tier, adhere to these constraints:

*   **Context Scoping:** Prevent "attention dilution" by providing only the relevant dependency graph rather than an entire repository dump. This improves token efficiency and model focus.
*   **Modular Decomposition:** Force the output into small, isolated functional blocks. This keeps the reasoning path manageable and maintains code cleanliness.
*   **Supervised Validation:** Treat all outputs as drafts. Regardless of the model's cost or "intelligence," validate the logic through automated tests and manual review before committing.
*   **Standards Injection:** Ensure project-level constraints (e.g., logging patterns, AWS SDK versions, function length) are always injected into the system prompt to maintain quality across all tiers.

## Workflow

1. **Load catalog** — Read `models-catalog.json` for `cursor_allowlist`, `tiers`, and `task_routing`.
2. **Categorize task** — `architectural` | `general` | `routine` (see [reference.md](reference.md) for signals).
3. **Resolve tier** — Map category → tier key → `tiers[tier].primary` (fallback: first `alternates[]`).
4. **Cross-check agent** — If using `@agent(NAME)`, prefer `agent_tier_hints[NAME]` when it matches task category; escalate tier when signals conflict (e.g. SECURITY review on auth → frontier even if file count is small).
5. **Apply execution discipline** — Context scoping, modular output, validation, standards (section 3 above).
6. **Spawn subagents** — Task tool: pass `model: "<slug>"` only from `cursor_allowlist`. If slug unavailable, state gap and use tier primary.
7. **User chat model** — Recommend tier + slug; user switches in Cursor model picker (Chat / Composer / Agent).

## Refresh catalog from web

When the user asks to update best-known models **within Cursor's lineup**:

```bash
python templates/skills/shared-practices/route-task-to-model/scripts/update-models-catalog.py --dry-run
python templates/skills/shared-practices/route-task-to-model/scripts/update-models-catalog.py --apply
```

Script rules:
- **Allowlist-only** — Never add slugs Cursor does not expose to Task/subagents.
- **Tier winners** — Re-rank `primary` / `alternates` per tier from fetched evidence.
- **Human review** — Default `--dry-run`; `--apply` writes `models-catalog.json` and appends `changelog`.
- **Agent sync (optional)** — After apply, offer to align `templates/agents/subagents/*.md` `model:` frontmatter with `agent_tier_hints` → tier `primary`.

## Output Contract

| Field | Content |
|-------|---------|
| **Task category** | `architectural` \| `general` \| `routine` |
| **Tier** | frontier \| mid_tier \| lightweight |
| **Recommended slug** | From `cursor_allowlist` |
| **Why** | One line tied to trade-off matrix |
| **Execution notes** | Context scope, validation step, standards to inject |
| **Escalate tier when** | Signals that override default (security, cross-file refactor, ambiguous spec) |

## Routing boundaries

- **Model vs agent vs skill** — This skill picks **model tier/slug** only. Domain ownership → `route-agent.ps1`; workflow steps → `route-skill.ps1`.
- **Token pressure** — Pair with `save-tokens-in-context` when context is large; tier down only if quality risk is acceptable.
- **Unavailable slug** — Do not substitute a non-allowlisted model; report and use closest tier primary.

## Additional resources

- Task signal examples and agent mapping: [reference.md](reference.md)
- Quick CLI: `~/.cursor/commands/route-model.ps1`
