# AVAILABLE SUBAGENTS

Subagents live in `.cursor/agents/` and appear in **Settings > Subagents**. Invoke via `@agent(NAME)` in chat or using the language's comment syntax with `@agent(NAME)` in code comments.

**Short names** (for invocation) vs **file names** (descriptive). Models chosen for cost vs quality: Opus only for critical reasoning (SECURITY, ARCHITECT); Sonnet for structured analysis; Composer for code-heavy tasks.

| Invoke | File | Model |
|--------|------|-------|
| PM | product_manager.md | claude-4.6-sonnet-medium-thinking |
| REVIEWER | code_reviewer.md | claude-4.6-sonnet-medium-thinking |
| TESTER | test_engineer.md | composer-2.5-fast |
| DOCS | documentation_writer.md | composer-2.5-fast |
| SECURITY | security_engineer.md | claude-opus-4-8-thinking-high |
| ARCHITECT | architecture_advisor.md | claude-opus-4-8-thinking-high |
| DEVOPS | devops_engineer.md | composer-2.5-fast |
| DATABASE_SQL | sql_database_engineer.md | composer-2.5-fast |
| DATABASE_NOSQL | nosql_database_engineer.md | composer-2.5-fast |
| FE_UI_ENGINEER | fe_ui_engineer.md | composer-2.5-fast |
| FE_UX_DESIGN | fe_ux_design.md | claude-4.6-sonnet-medium-thinking |
| FE_DESIGN_SYSTEM | fe_design_system.md | claude-4.6-sonnet-medium-thinking |
| FE_STATE_ENGINEER | fe_state_engineer.md | composer-2.5-fast |
| FE_TEST_ENGINEER | fe_test_engineer.md | composer-2.5-fast |
| FE_CODE_REVIEWER | fe_code_reviewer.md | claude-4.6-sonnet-medium-thinking |
| FE_ACCESSIBILITY_ENGINEER | fe_accessibility_engineer.md | claude-4.6-sonnet-medium-thinking |
| FE_PERFORMANCE_ENGINEER | fe_performance_engineer.md | claude-4.6-sonnet-medium-thinking |
| BACKEND_PYTHON | backend_python_engineer.md | composer-2.5-fast |
| BACKEND_GO | backend_go_engineer.md | composer-2.5-fast |
| PERFORMANCE | performance_engineer.md | claude-4.6-sonnet-medium-thinking |
| DATA_ENGINEER | data_engineer.md | composer-2.5-fast |
| INCIDENT | incident_responder.md | claude-4.6-sonnet-medium-thinking |
| AI_PLATFORM | ai_platform_engineer.md | composer-2.5-fast |
| BOT_DESIGNER | bot_conversation_designer.md | claude-4.6-sonnet-medium-thinking |
| AI_SAFETY | ai_safety_engineer.md | claude-opus-4-8-thinking-high |
| AI_OBSERVABILITY | ai_observability_engineer.md | claude-4.6-sonnet-medium-thinking |
| RAG_ENGINEER | rag_engineer.md | composer-2.5-fast |
| AI_SYSTEM_REVIEWER | llm_system_reviewer.md | claude-4.6-sonnet-medium-thinking |

## CORE SUBAGENTS

### PM (product_manager.md)
Task breakdown, planning, execution. Parse input files, generate specs in `specs/`. Prioritization, acceptance criteria, sprint planning.

### REVIEWER (code_reviewer.md)
Code review. Type safety, architecture, security, performance, maintainability. Direct feedback with severity (CRITICAL/WARNING/GOOD).

### TESTER (test_engineer.md)
Test generation. pytest, AAA, edge cases, mocking. One file per module, one class per function.

### DOCS (documentation_writer.md)
Documentation. API docs, README, architecture. Scannable format, examples, imperative mood.

### SECURITY (security_engineer.md)
Security audit. OWASP, HIPAA/GDPR. Input validation, secrets, dependencies. Severity-based reporting.

### ARCHITECT (architecture_advisor.md)
Architecture. Scalability, coupling, patterns. ADRs, tradeoff analysis, migration paths.

## SPECIALIZED SUBAGENTS

### DEVOPS (devops_engineer.md)
Infrastructure, CI/CD, Docker, monitoring. Idempotent deployments, runbooks.

### DATABASE_SQL (sql_database_engineer.md)
Relational DB. Schema design, migrations, query optimization, EXPLAIN plans.

### DATABASE_NOSQL (nosql_database_engineer.md)
MongoDB, DynamoDB, Cassandra. Access pattern design, partition keys, denormalization.

### FE_UI_ENGINEER (fe_ui_engineer.md)
Frontend component/page implementation. React/TypeScript UI, responsive layout, semantic structure.

### FE_UX_DESIGN (fe_ux_design.md)
Frontend UX design. User flows, interaction behavior, edge states, implementation-ready criteria.

### FE_DESIGN_SYSTEM (fe_design_system.md)
Frontend design system. Tokens, reusable component contracts, visual consistency and theming constraints.

### FE_STATE_ENGINEER (fe_state_engineer.md)
Frontend state management. Client/server state boundaries, caching policy, invalidation, optimistic updates.

### FE_TEST_ENGINEER (fe_test_engineer.md)
Frontend testing. RTL/Vitest/Playwright coverage, regression protection, flake reduction.

### FE_CODE_REVIEWER (fe_code_reviewer.md)
Frontend code review. Correctness, state-flow regressions, accessibility/performance risks, and test sufficiency in UI changes.

### FE_ACCESSIBILITY_ENGINEER (fe_accessibility_engineer.md)
Frontend accessibility. Keyboard/focus behavior, semantic structure, ARIA correctness, WCAG-oriented remediation.

### FE_PERFORMANCE_ENGINEER (fe_performance_engineer.md)
Frontend performance. Core Web Vitals, bundle/render profiling, code-splitting and loading-path optimization.

## BACKEND SPECIALIZED SUBAGENTS

### BACKEND_PYTHON (backend_python_engineer.md)
FastAPI/Django, async, Pydantic, SQLAlchemy. Security-first, type hints, pytest.

### BACKEND_GO (backend_go_engineer.md)
Gin/Echo, GORM, idiomatic Go. Error handling, table-driven tests, benchmarks.

### PERFORMANCE (performance_engineer.md)
Profiling, bottlenecks, complexity. Measure before optimize. Database, API, caching.

### DATA_ENGINEER (data_engineer.md)
ETL/ELT, pipelines, data quality. Idempotent, incremental, Airflow/Prefect/Dagster.

### INCIDENT (incident_responder.md)
Debugging and production incidents. Reproduce, isolate, evidence-driven RCA. Mitigation vs remediation. Logs, metrics, traces; minimal repro; postmortem structure. Redact secrets in evidence.

## AI INFRASTRUCTURE SUBAGENTS

### AI_PLATFORM (ai_platform_engineer.md)
Bot gateway, channel adapters, sessions, rate limits, policy middleware, scaling.

### BOT_DESIGNER (bot_conversation_designer.md)
Customer conversation flows, persona, handoff, end-user tone. Runtime personas live in `templates/ai-runtime/bots/examples/`.

### AI_SAFETY (ai_safety_engineer.md)
Prompt injection, content policy, tool risk, OWASP LLM, red-team review.

### AI_OBSERVABILITY (ai_observability_engineer.md)
LLM traces, audit logs, evals, SLOs, incident correlation.

### RAG_ENGINEER (rag_engineer.md)
Corpus ingest, chunking, embeddings, vector index, hybrid retrieval, citations. Escalates ETL to `DATA_ENGINEER`.

### AI_SYSTEM_REVIEWER (llm_system_reviewer.md)
LLM system design review (not code review). Twelve-dimension checklist: hallucination, context, retrieval, observability, tenant isolation, cost/latency. Escalates implementation to `AI_SAFETY`, `RAG_ENGINEER`, `AI_PLATFORM`, `AI_OBSERVABILITY`.

## RULES (TECHNICAL STANDARDS)

Rules in `.cursor/rules/*.mdc` add technical depth and apply via globs. **Catalog:** [rules/RULES.md](../rules/RULES.md). **Audit:** `~/.cursor/commands/route-rules.ps1`.

**Navigation hub:** [USAGE.md](../USAGE.md).

## POLICY PRECEDENCE

When guidance conflicts, apply this order:

1. **Security and safety constraints first** (never override these).
2. **Scoped rules** in `.cursor/rules/*.mdc` for matching files.
3. **Workflow skills** (`.cursor/skills/**/SKILL.md`; source: `templates/skills/**`) for task execution steps.
4. **Subagent prompt** (`.cursor/agents/*.md`; source: `templates/agents/subagents/*.md`) for domain ownership and output style.
5. **Examples/docs** (`README`, usage snippets) as non-authoritative guidance.

Tie-breaks:

- Prefer the more specific scope over generic guidance.
- Prefer explicit project contract/policy over framework default.
- For frontend-local work, prefer `FE_*`; escalate cross-stack/system-wide to generic specialists (`TESTER`, `PERFORMANCE`, `SECURITY`, etc.).

## SYNC

Author under `templates/agents/subagents/*.md` in **Cursor-Usage-Templates**, then publish to global and run `FromGlobal` in consumer projects. See `templates/MAINTAINER.md` in that repo.

## Note:
Codex will review your results of the review for double-check.