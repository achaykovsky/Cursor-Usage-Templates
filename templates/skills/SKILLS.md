# Skills Catalog

Skills sync to `.cursor/skills/**/SKILL.md` from `templates/skills/**/SKILL.md`. **Author under `templates/skills/`** — the agent **reads a skill when the task matches** its YAML `description` — you rarely need to paste skill bodies.

**Start:** [USAGE.md](../USAGE.md) intent table. **Multi-FE:** use `orchestrate-frontend-delivery` first.

Format: `skill-name` | trigger phrases | optional `@agent`

---

## api-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `create-fastapi` | scaffold FastAPI, new API project | `BACKEND_PYTHON` |
| `create-flask-api` | scaffold Flask API | `BACKEND_PYTHON` |
| `implement-or-extend-api-surface` | new endpoint, implement API, OpenAPI | `BACKEND_PYTHON` / `BACKEND_GO` |
| `validate-api-contract` | spec vs implementation drift | `REVIEWER` |
| `check-api-backward-compatibility` | breaking?, safe for clients | `ARCHITECT` |
| `review-openapi-diff` | OpenAPI diff review | `REVIEWER` |
| `manage-request-response-schema-changes` | schema evolution, required fields | `BACKEND_*` |
| `api-versioning-guidance` | v2, deprecate endpoint | `ARCHITECT` |
| `analyze-api-consumer-impact` | who breaks, consumer impact | `PM` |

## architecture-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `evaluate-architecture-tradeoffs` | compare designs, tradeoffs | `ARCHITECT` |
| `select-architecture-patterns-pragmatically` | service boundaries, CQRS, layering | `ARCHITECT` |
| `plan-architecture-evolution` | major refactor, split services | `ARCHITECT` |

## code-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `design-feature-from-requirements` | user story → design | `PM` |
| `fix-bug-systematically` | fix bug, root cause | `INCIDENT` |
| `refactor-safely` | refactor, rename, cleanup | `REVIEWER` |
| `add-logging-to-code` | add logging, debug path | — |
| `add-comments-to-code` | add comments, document code, explain function | — |
| `add-error-handling-to-code` | add error handling, custom/specific exceptions | — |
| `audit-codebase-cleanup` | dead code, duplication audit | `REVIEWER` |
| `review-architecture-fit` | does this fit architecture | `ARCHITECT` |
| `review-pull-request` | PR review, address review comments, review this change | `REVIEWER` |

## config-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `audit-config-and-secrets` | audit secrets, leaked credentials | `SECURITY` |

## dependency-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `assess-and-update-dependencies` | upgrade deps, CVEs | `SECURITY` |
| `reproduce-environment-from-docs` | setup dev env, get running | `DEVOPS` |

## devops-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `design-ci-cd-pipeline` | design CI/CD | `DEVOPS` |
| `implement-ci-cd-pipeline` | implement CI YAML | `DEVOPS` |
| `design-terraform-infrastructure` | plan Terraform layout | `DEVOPS` |
| `implement-terraform-modules` | write Terraform | `DEVOPS` |
| `design-cloudformation-stacks` | plan CFN stacks | `DEVOPS` |
| `implement-cloudformation-stacks` | write CFN templates | `DEVOPS` |
| `validate-infra-changes-pre-apply` | pre-apply Terraform/CFN | `DEVOPS` |

## docs-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `keep-docs-in-sync-with-code` | update docs after change | `DOCS` |
| `write-or-update-adr` | ADR, architecture decision | `ARCHITECT` |

## frontend-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `orchestrate-frontend-delivery` | **multi-FE ownership unclear** | routes FE agents |
| `design-ux-flow-spec` | UX flow, state matrix | `FE_UX_DESIGN` |
| `evolve-design-system-without-breaking-ui` | tokens, component variants | `FE_DESIGN_SYSTEM` |
| `implement-accessible-ui-from-spec` | build UI from spec | `FE_UI_ENGINEER` |
| `architect-frontend-state-and-cache` | React Query, stale data, races | `FE_STATE_ENGINEER` |
| `review-frontend-code` | FE PR review | `FE_CODE_REVIEWER` |
| `review-frontend-accessibility` | a11y, WCAG, keyboard | `FE_ACCESSIBILITY_ENGINEER` |
| `add-frontend-tests-for-change` | RTL, Vitest, Playwright | `FE_TEST_ENGINEER` |
| `optimize-core-web-vitals` | LCP, INP, CLS, bundle | `FE_PERFORMANCE_ENGINEER` |

**FE sequence** (when not using orchestrator): UX → design-system → UI → state → review → a11y → tests → perf.

## git-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `explain-and-navigate-git-history` | blame, when did X change | — |
| `prepare-atomic-commit` | split commits, commit message | — |

## migration-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `plan-and-execute-migration` | migrate schema/data/config | `DATABASE_SQL` / `DATA_ENGINEER` |
| `handle-breaking-change` | breaking change, deprecate API | `ARCHITECT` |

## navigation-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `explain-codebase-structure` | explain repo, where is X | — |
| `organize-project-structure` | restructure folders | `ARCHITECT` |
| `trace-data-flow` | trace data path end-to-end | — |

## performance-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `investigate-performance-issue` | slow, optimize, regression | `PERFORMANCE` |
| `add-observability-for-debugging` | metrics, traces, prod debug | `PERFORMANCE` |
| `design-batching-strategy` | batching, N+1, bulk ops | `PERFORMANCE` |

## qa-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `design-risk-based-test-plan` | QA scope, test plan | `PM` |
| `execute-qa-test-cycle` | run QA cycle | `TESTER` |
| `triage-and-prioritize-defects` | bug triage, priority | `PM` |
| `manage-regression-test-suite` | flaky tests, suite hygiene | `TESTER` |
| `perform-release-readiness-signoff` | QA signoff before release | `PM` |

## release-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `prepare-release` | changelog, tag, cut release | `DEVOPS` |
| `validate-pre-deploy` | ready to deploy, pre-flight | `DEVOPS` |

## security-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `security-scan-changes` | security review of diff | `SECURITY` |
| `sensitive-data-handling` | PII, HIPAA, GDPR in code | `SECURITY` |

## shared-practices

| Skill | Triggers | Agent |
|-------|----------|-------|
| `route-task-to-model` | pick model, model tier, cost vs quality, Task model= | — |
| `save-tokens-in-context` | large context, token savings | — |
| `redact-sensitive-in-output` | redact output, no secrets in reply | — |
| `suggest-commands-dont-run-destructive` | destructive git/deploy caution | — |

## testing-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `add-tests-for-change` | add tests after change | `TESTER` |
| `reproduce-and-document-failure` | paste error, reproduce bug | `INCIDENT` |

## eval-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `design-prompt-evals` | prompt eval, golden dataset, eval suite, regression eval, benchmark prompts | `AI_OBSERVABILITY` |
| `implement-prompt-eval-runner` | implement eval runner, CI eval job, pytest prompt eval, run golden questions | `BACKEND_PYTHON` / `AI_OBSERVABILITY` |
| `calibrate-llm-judge-eval` | LLM judge, rubric eval, model-as-judge, faithfulness scorer, calibrate judge threshold | `AI_OBSERVABILITY` |

## ai-infra-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `orchestrate-ai-bot-delivery` | **multi-step bot**, customer agent, chatbot platform | routes AI_* / BOT_* |
| `design-customer-facing-agent` | support bot, chatbot spec, FAQ agent | `BOT_DESIGNER` |
| `implement-bot-gateway` | bot gateway, webhooks, LLM API service | `AI_PLATFORM` |
| `add-prompt-injection-defenses` | prompt injection, jailbreak, untrusted input | `AI_SAFETY` |
| `design-ai-observability` | LLM traces, bot audit, eval pipeline | `AI_OBSERVABILITY` |
| `implement-human-handoff` | escalate to human, ticket, handoff | `BOT_DESIGNER` |
| `evaluate-ai-safety-policy` | content policy, PII in context, retention | `AI_SAFETY` |
| `design-multi-agent-routing` | router bot, specialist delegation | `AI_PLATFORM` |
| `implement-ai-rate-limiting` | rate limit, abuse, cost cap | `AI_PLATFORM` |
| `monitor-ai-quality` | eval drift, quality regression, thumbs feedback | `AI_OBSERVABILITY` |
| `review-llm-system-design` | llm system design review, bot architecture review, hallucination risks, tenant isolation | `AI_SYSTEM_REVIEWER` |

## rag-workflows

| Skill | Triggers | Agent |
|-------|----------|-------|
| `orchestrate-rag-delivery` | **multi-step RAG**, knowledge base, vector search | routes RAG_ENGINEER / delegates |
| `design-rag-architecture` | corpus design, hybrid retrieval, vector store | `RAG_ENGINEER` |
| `implement-rag-ingest-and-index` | ingest, chunk, embed, index | `RAG_ENGINEER` |
| `implement-retrieval-pipeline` | retrieve, rerank, cite, search_knowledge_base | `RAG_ENGINEER` |

## langchain-workflows (optional)

| Skill | Triggers | Agent |
|-------|----------|-------|
| `implement-rag-with-langchain-stack` | LangChain/LangGraph/LangSmith RAG | `RAG_ENGINEER` |

---

## Escalation (avoid duplicate work)

| FE-local | Escalate to |
|----------|-------------|
| Component, a11y, CWV | `FE_*` agents / frontend skills |
| Cross-stack tests | `TESTER` |
| Backend/DB/infra perf | `PERFORMANCE` |
| Security/compliance | `SECURITY` |

Unsure? Paste [plan-cursor-skills-routing.md](../prompts/plan-cursor-skills-routing.md) with your task one-liner — not this file.

## Note
Codex will review your results for double-check.