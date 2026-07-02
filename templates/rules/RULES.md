# Rules Catalog

Rules sync to `.cursor/rules/` from `templates/rules/`. They load **automatically** when you edit files matching `globs`, or always when `alwaysApply: true`. You do not invoke rules in chat.

**Precedence:** security/safety → scoped rules (this doc) → skills → agents. See [USAGE.md](../USAGE.md).

---

## Always applied

| Rule | Focus |
|------|-------|
| `security.mdc` | OWASP, secrets, auth, injection, dependencies |
| `ai-guardrails.mdc` | Ground truth, minimal diffs, mandatory logging/comments on new code |
| `observability.mdc` | Logs, metrics, traces, audit, redaction |
| `token-efficiency.mdc` | Concise I/O, references over pastes |
| `mcp-integrations.mdc` | MCP safety + CLI-first token routing; approval for writes |
| `resource-usage-report.mdc` | Agent prepends Resources used table (full enumeration; rules, skills, agents, MCP, hooks) |
| `performance.mdc` | Profiling, complexity, N+1 (always applied) |
| `git-github-workflow.mdc` | Merge commits, append-only history, CI-before-merge, PR review resolution |

---

## File-scoped (by glob)

| Rule | Globs | Focus |
|------|-------|-------|
| `python-backend.mdc` | `**/*.py` | FastAPI, typing, pytest, specific exceptions |
| `go-backend.mdc` | `**/*.go` | Idiomatic Go, tests |
| `frontend.mdc` | `**/*.{tsx,jsx,vue,css,scss}` | React/TS, a11y, UX |
| `sql-database.mdc` | `**/*.sql`, migrations, alembic | Schema, queries |
| `nosql-database.mdc` | models, mongo, dynamodb paths | Access patterns |
| `api-contract.mdc` | api, openapi, router paths | Status codes, versioning |
| `architecture.mdc` | `**/*.{py,go,ts,tsx,js,jsx,vue}` | Layers, coupling, ADRs |
| `clean-code.mdc` | code extensions | Naming, SRP, DRY, readability, YAGNI |
| `code-review.mdc` | code extensions | Review quality bar |
| `testing.mdc` | test file patterns | pytest, AAA, coverage, portable Code Runner + CLI entry |
| `documentation.mdc` | `**/*.md`, docs | README, API docs, ADR shape |
| `planning.mdc` | `**/specs/**` | Specs, acceptance criteria |
| `devops.mdc` | Dockerfile, CI, `**/*.tf` | CI/CD, containers, IaC |
| `data-pipelines.mdc` | dags, pipelines, etl | ETL idempotency |
| `skills-consistency.mdc` | `.cursor/skills/**/SKILL.md` (template source: `templates/skills/**`) | Skill structure/routing |

### AI / bot / RAG (file-scoped)

| Rule | Globs | Focus |
|------|-------|-------|
| `ai-customer-facing.mdc` | `**/bots/**`, `**/ai-runtime/**`, `**/ai-gateway/**` | Tone, disclaimers, no internal leakage, handoff |
| `ai-safety.mdc` | `**/bots/**`, `**/ai-runtime/**`, `**/ai-gateway/**`, `**/prompts/**` | Input boundary, tool allowlist, injection defense |
| `ai-pii.mdc` | `**/bots/**`, `**/ai-gateway/**`, `**/rag/**` | PII minimization, retention, RAG corpus controls |
| `llm-gateway.mdc` | `**/ai-gateway/**`, `**/bots/**/gateway/**` | Timeouts, retries, circuit breakers, structured errors |
| `rag-pipeline.mdc` | `**/rag/**`, `**/retrieval/**`, `**/embeddings/**`, `**/vector/**` | Ingest, chunk metadata, hybrid retrieval, cite-or-abstain |

---

## Overlap notes (efficient routing)

- **Python API file** → `python-backend` + `architecture` + `clean-code` + `performance` + always-applied.
- **TSX component** → `frontend` + `architecture` + `clean-code` + `performance` + always-applied.
- **OpenAPI / router** → `api-contract` + language rule for implementation files.
- **Editing a skill** → `skills-consistency` only (plus always-applied).
- **Bot manifest / ai-runtime JSON** → `ai-customer-facing` + `ai-safety` + `python-backend` (for `.py`) + always-applied.
- **RAG corpus / retrieval code** → `rag-pipeline` + `ai-pii` + `data-pipelines` (ETL) + always-applied.

When unsure which rules apply to a path, paste [plan-cursor-rules-audit.md](../prompts/plan-cursor-rules-audit.md) with file list — do not paste this whole file.

---

## Usage

- **Authors:** add `.mdc` with `description`, `globs`, `alwaysApply` in frontmatter; update this table.
- **Consumers:** no action — rules apply on edit. Override only via explicit project policy in `project.md` (must not weaken security).

## Note
Codex will review your results for double-check.
