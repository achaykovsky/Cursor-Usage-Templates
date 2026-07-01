"""Keyword tables and scoring helpers shared by all routers."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Iterable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuleEntry:
    name: str
    globs: tuple[str, ...]


ALWAYS_APPLIED_RULES: tuple[str, ...] = (
    "security.mdc",
    "ai-guardrails.mdc",
    "observability.mdc",
    "token-efficiency.mdc",
    "mcp-integrations.mdc",
    "resource-usage-report.mdc",
    "performance.mdc",
)

FILE_SCOPED_RULES: tuple[RuleEntry, ...] = (
    RuleEntry("python-backend.mdc", ("**/*.py",)),
    RuleEntry("go-backend.mdc", ("**/*.go",)),
    RuleEntry("frontend.mdc", ("**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.css", "**/*.scss")),
    RuleEntry("sql-database.mdc", ("**/*.sql", "**/migrations/**", "**/alembic/**")),
    RuleEntry("nosql-database.mdc", ("**/models/**", "**/mongo/**", "**/dynamodb/**")),
    RuleEntry("api-contract.mdc", ("**/api/**", "**/openapi/**", "**/router/**")),
    RuleEntry("architecture.mdc", ("**/*.py", "**/*.go", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/*.vue")),
    RuleEntry("code-review.mdc", ("**/*.py", "**/*.go", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx")),
    RuleEntry("testing.mdc", ("**/test_*.py", "**/*_test.go", "**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts")),
    RuleEntry("documentation.mdc", ("**/*.md", "**/docs/**")),
    RuleEntry("planning.mdc", ("**/specs/**",)),
    RuleEntry("devops.mdc", ("**/Dockerfile", "**/.github/**", "**/*.tf", "**/ci/**")),
    RuleEntry("data-pipelines.mdc", ("**/dags/**", "**/pipelines/**", "**/etl/**")),
    RuleEntry("skills-consistency.mdc", ("**/.cursor/skills/**/SKILL.md", "**/templates/skills/**/SKILL.md")),
    RuleEntry("ai-customer-facing.mdc", ("**/bots/**", "**/ai-runtime/**", "**/ai-gateway/**")),
    RuleEntry("ai-safety.mdc", ("**/bots/**", "**/ai-runtime/**", "**/ai-gateway/**", "**/prompts/**")),
    RuleEntry("ai-pii.mdc", ("**/bots/**", "**/ai-gateway/**", "**/rag/**")),
    RuleEntry("rag-pipeline.mdc", ("**/rag/**", "**/retrieval/**", "**/embeddings/**", "**/vector/**")),
)

# Distinctive phrases per skill — avoid bare terms shared across domains (e.g. "release", "cleanup").
SKILL_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # api-workflows
    ("create-fastapi", ("create fastapi", "scaffold fastapi", "new fastapi project", "fastapi scaffold")),
    ("create-flask-api", ("create flask", "scaffold flask", "new flask project", "flask scaffold")),
    (
        "implement-or-extend-api-surface",
        ("new endpoint", "implement endpoint", "implement api", "extend api", "fastapi", "flask", "openapi", "rest endpoint"),
    ),
    ("validate-api-contract", ("api contract", "contract drift", "spec vs implementation", "match the api")),
    ("review-openapi-diff", ("openapi diff", "spec diff", "swagger diff", "what changed in openapi")),
    (
        "manage-request-response-schema-changes",
        ("schema evolution", "request schema", "response schema", "required fields"),
    ),
    (
        "check-api-backward-compatibility",
        ("backward compat", "backward compatible", "is this breaking", "safe for clients"),
    ),
    ("api-versioning-guidance", ("api version", "deprecate endpoint", "api v2", "version api")),
    ("analyze-api-consumer-impact", ("consumer impact", "who breaks", "blast radius", "api consumers")),
    # architecture-workflows
    ("evaluate-architecture-tradeoffs", ("architecture tradeoff", "compare designs", "design tradeoff")),
    (
        "select-architecture-patterns-pragmatically",
        ("service boundaries", "cqrs", "layering", "architecture pattern"),
    ),
    ("plan-architecture-evolution", ("split services", "architecture evolution", "architecture drift")),
    # code-workflows
    ("design-feature-from-requirements", ("requirements", "user story", "feature spec", "design feature")),
    ("fix-bug-systematically", ("fix bug", "root cause", "debug session", "defect")),
    ("reproduce-and-document-failure", ("reproduce", "failing test", "paste error", "minimal repro")),
    (
        "audit-codebase-cleanup",
        (
            "dead code",
            "duplication",
            "duplicate",
            "redundant",
            "clean up",
            "clean-up",
            "cleanup",
            "code clean",
            "maintainability",
            "legacy code",
            "obsolete",
        ),
    ),
    ("refactor-safely", ("refactor", "rename", "extract function", "restructure code", "move module")),
    ("add-logging-to-code", ("add logging", "log this", "debug path", "structured log")),
    (
        "add-comments-to-code",
        ("add comment", "add comments", "document this", "explain this", "docstring", "inline comment"),
    ),
    (
        "add-error-handling-to-code",
        (
            "add error handling",
            "error handling",
            "raise exception",
            "custom exception",
            "specific exception",
            "except block",
            "domain error",
        ),
    ),
    ("review-architecture-fit", ("architecture fit", "fit our architecture", "module boundar", "new subsystem")),
    ("review-pull-request", ("pull request", "code review", "pr review", "clean-code", " review ")),
    # config / dependency
    ("audit-config-and-secrets", ("audit secrets", "leaked credentials", "credentials in repo", ".env leak")),
    (
        "assess-and-update-dependencies",
        ("update deps", "upgrade dependencies", "dependency audit", "cve in dependencies"),
    ),
    ("reproduce-environment-from-docs", ("dev environment", "get this running", "set up dev", "onboard locally")),
    # devops-workflows
    ("design-ci-cd-pipeline", ("design ci/cd", "design pipeline", "ci/cd design")),
    (
        "implement-ci-cd-pipeline",
        ("implement ci/cd", "github actions", "ci yaml", "continuous integration"),
    ),
    ("design-terraform-infrastructure", ("design terraform", "terraform layout", "terraform architecture")),
    ("implement-terraform-modules", ("terraform module", "write terraform", "terraform code")),
    ("design-cloudformation-stacks", ("design cloudformation", "cfn stacks", "cloudformation layout")),
    ("implement-cloudformation-stacks", ("cloudformation template", "write cloudformation", "cfn template")),
    ("validate-infra-changes-pre-apply", ("terraform plan", "pre-apply", "infra validation", "cfn change set")),
    # docs-workflows
    ("keep-docs-in-sync-with-code", ("sync docs", "update readme", "docs out of date", "docs after change")),
    ("write-or-update-adr", ("write adr", "architecture decision record", "document this decision")),
    # frontend-workflows
    (
        "orchestrate-frontend-delivery",
        ("multi-fe", "frontend delivery", "fe ownership", "react component", "ui page", "ux to ui"),
    ),
    ("design-ux-flow-spec", ("ux flow", "user journey", "state matrix", "interaction design")),
    ("evolve-design-system-without-breaking-ui", ("design tokens", "component variants", "design system migration")),
    ("implement-accessible-ui-from-spec", ("build ui", "implement component", "accessible ui", "from mockup")),
    (
        "architect-frontend-state-and-cache",
        ("react query", "cache invalidation", "frontend state", "optimistic update"),
    ),
    ("review-frontend-code", ("frontend review", "tsx review", "react review", "fe pr")),
    ("review-frontend-accessibility", ("wcag", "keyboard navigation", "accessibility review", "aria audit")),
    ("add-frontend-tests-for-change", ("rtl", "vitest", "playwright", "frontend test")),
    ("optimize-core-web-vitals", ("lcp", "cls", "inp", "core web vitals", "bundle size")),
    # git-workflows
    ("explain-and-navigate-git-history", ("git blame", "git history", "when did this change", "who touched")),
    ("prepare-atomic-commit", ("commit message", "split commits", "atomic commit", "conventional commit")),
    # migration-workflows
    ("handle-breaking-change", ("breaking change migration", "deprecation window", "breaking migration")),
    ("plan-and-execute-migration", ("schema migration", "data migration", "migrate off", "migrate schema")),
    # navigation-workflows
    ("explain-codebase-structure", ("where is", "explain repo", "navigate codebase", "codebase map")),
    ("organize-project-structure", ("restructure", "folder layout", "organize project", "where should x go")),
    ("trace-data-flow", ("trace request", "data flow", "follow this flow", "where does this value")),
    # performance-workflows
    ("investigate-performance-issue", ("performance issue", "slow request", "latency spike", "profile bottleneck")),
    (
        "add-observability-for-debugging",
        ("instrument service", "production debug", "add metrics", "distributed trace"),
    ),
    ("design-batching-strategy", ("batching strategy", "bulk operations", "n+1", "chunking")),
    # qa-workflows
    ("design-risk-based-test-plan", ("test plan", "qa scope", "risk-based test")),
    ("execute-qa-test-cycle", ("qa cycle", "execute qa", "test execution cycle")),
    ("triage-and-prioritize-defects", ("bug triage", "defect priority", "prioritize bugs")),
    ("manage-regression-test-suite", ("flaky test", "regression suite", "test suite hygiene")),
    (
        "perform-release-readiness-signoff",
        ("qa signoff", "release signoff", "release readiness", "release approval"),
    ),
    # release-workflows — no bare "release" on pre-deploy; reserve release phrases for cut/signoff skills
    ("prepare-release", ("changelog", "version bump", "cut release", "tag release", "prepare release")),
    (
        "validate-pre-deploy",
        ("pre-deploy", "pre-flight", "ready to deploy", "can we ship", "pre-deploy check"),
    ),
    # security-workflows
    ("security-scan-changes", ("security review", "security risk", "vulnerability", "vuln", "cve", "owasp")),
    ("sensitive-data-handling", ("pii", "hipaa", "gdpr", "regulated data", "patient data")),
    # shared-practices
    ("route-task-to-model", ("pick model", "model tier", "task model", "route to model")),
    ("save-tokens-in-context", ("save tokens", "token savings", "reduce tokens", "long chat cost")),
    ("redact-sensitive-in-output", ("redact output", "no secrets in output", "redact sensitive")),
    (
        "suggest-commands-dont-run-destructive",
        ("destructive command", "dont run deploy", "suggest commands", "without running"),
    ),
    # testing-workflows
    ("add-tests-for-change", ("add tests", "pytest", "test coverage", "unit test")),
    # ai-infra-workflows
    (
        "orchestrate-ai-bot-delivery",
        ("customer bot", "chatbot", "support bot", "ai platform", "bot delivery", "multi-step bot"),
    ),
    (
        "design-customer-facing-agent",
        ("customer-facing agent", "support bot spec", "chatbot design", "faq bot", "conversation flow"),
    ),
    (
        "implement-bot-gateway",
        ("bot gateway", "llm gateway", "webhook bot", "fastapi bot", "chat api"),
    ),
    (
        "add-prompt-injection-defenses",
        ("prompt injection", "jailbreak", "untrusted input", "injection defense"),
    ),
    (
        "design-ai-observability",
        ("llm traces", "bot audit", "ai observability", "eval pipeline"),
    ),
    (
        "implement-human-handoff",
        ("human handoff", "escalate to human", "talk to agent", "human queue"),
    ),
    (
        "evaluate-ai-safety-policy",
        ("ai safety policy", "content policy", "pii in context", "bot retention"),
    ),
    (
        "design-multi-agent-routing",
        ("router bot", "multi-agent", "specialist bot", "agent routing"),
    ),
    (
        "implement-ai-rate-limiting",
        ("rate limit bot", "abuse control", "cost cap", "token budget"),
    ),
    (
        "monitor-ai-quality",
        ("ai quality", "eval regression", "bot drift", "thumbs feedback"),
    ),
    # rag-workflows
    (
        "orchestrate-rag-delivery",
        ("rag pipeline", "knowledge base", "vector search", "document corpus", "build rag"),
    ),
    (
        "design-rag-architecture",
        ("rag architecture", "corpus design", "vector store choice", "hybrid retrieval"),
    ),
    (
        "implement-rag-ingest-and-index",
        ("ingest documents", "chunk documents", "embed corpus", "vector index", "reindex"),
    ),
    (
        "implement-retrieval-pipeline",
        ("retrieval pipeline", "rerank", "semantic search", "search_knowledge_base"),
    ),
    # langchain-workflows (optional)
    (
        "implement-rag-with-langchain-stack",
        ("langchain rag", "langgraph rag", "langsmith eval", "langchain retrieval"),
    ),
)

AGENT_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("FE_UI_ENGINEER", ("ui", "component", "tsx", "jsx", "react", "layout")),
    ("FE_UX_DESIGN", ("ux", "user flow", "wireframe", "interaction")),
    ("FE_DESIGN_SYSTEM", ("design system", "tokens", "theming")),
    ("FE_STATE_ENGINEER", ("state", "cache", "react query", "redux")),
    ("FE_TEST_ENGINEER", ("frontend test", "rtl", "vitest", "playwright")),
    ("FE_CODE_REVIEWER", ("frontend review", "fe pr")),
    ("FE_ACCESSIBILITY_ENGINEER", ("a11y", "accessibility", "wcag", "aria")),
    ("FE_PERFORMANCE_ENGINEER", ("core web vitals", "lcp", "bundle size")),
    ("BACKEND_PYTHON", ("python", "fastapi", "django", "pydantic")),
    ("BACKEND_GO", ("golang", " go ", "gin", "echo")),
    ("DEVOPS", ("terraform", "docker", "ci/cd", "kubernetes", "infra")),
    ("DATABASE_SQL", ("sql", "postgres", "migration", "alembic")),
    ("DATABASE_NOSQL", ("mongo", "dynamodb", "nosql")),
    ("SECURITY", ("security audit", "threat model", "owasp", "hipaa")),
    ("ARCHITECT", ("architecture", "adr", "tradeoff", "system design")),
    ("INCIDENT", ("incident", "outage", "production down", "on-call")),
    ("PERFORMANCE", ("performance", "profil", "bottleneck")),
    ("TESTER", ("test", "pytest", "coverage")),
    ("DOCS", ("documentation", "readme", "api docs")),
    ("PM", ("plan", "roadmap", "acceptance criteria", "priorit")),
    ("REVIEWER", ("review", "pr", "pull request")),
    ("DATA_ENGINEER", ("etl", "pipeline", "airflow", "spark")),
    ("AI_PLATFORM", ("bot gateway", "llm gateway", "ai platform", "rate limit bot")),
    ("BOT_DESIGNER", ("conversation design", "chatbot flow", "bot persona", "handoff")),
    ("AI_SAFETY", ("prompt injection", "jailbreak", "llm security", "ai safety")),
    ("AI_OBSERVABILITY", ("llm trace", "bot audit", "ai eval", "bot slo")),
    ("RAG_ENGINEER", ("rag", "knowledge base", "vector search", "embedding index", "retrieval pipeline")),
)

MODEL_CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("architectural", ("architecture", "design", "tradeoff", "multi-file", "refactor", "security model")),
    ("routine", ("typo", "comment", "rename", "format", "boilerplate", "simple", "one-line")),
)

GATE_HOOKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("block-destructive-shell", ("rm ", "drop ", "truncate", "reset --hard")),
    ("validate-git-commands", ("git commit", "git push", "force")),
    ("validate-pre-push", ("git push", "pytest", "npm test")),
    ("validate-db-shell-operations", ("psql", "mysql", "alembic", "migrate", "drop table")),
    ("validate-mcp-operations", ("mcp", "deploy", "create", "delete")),
    ("redact-sensitive-read", (".env", ".pem", "credentials", "secret")),
)

PROMPT_RULE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("python-backend.mdc", ("python", "pytest", "poetry", "fastapi", "django", "pydantic")),
    ("go-backend.mdc", (" go ", "golang", " gin ", " echo ")),
    ("frontend.mdc", ("react", "tsx", "jsx", "frontend", " ui ", " ux ", "css", "vue")),
    ("api-contract.mdc", ("api", "openapi", "endpoint", "swagger", "rest")),
    ("testing.mdc", ("test", "coverage", "assert", "unit test")),
    ("documentation.mdc", ("doc", "readme", "adr", "markdown", "documentation")),
    ("sql-database.mdc", ("sql", "postgres", "migration", "alembic")),
    ("devops.mdc", ("terraform", "docker", "kubernetes", "ci/cd", "pipeline", "deploy")),
    ("architecture.mdc", ("architecture", "adr", "tradeoff", "system design")),
    ("rag-pipeline.mdc", ("rag", "knowledge base", "vector", "embedding", "retrieval", "corpus")),
)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def score_keywords(task: str, keywords: Iterable[str]) -> int:
    t = norm(task)
    return sum(1 for kw in keywords if kw in t)


def pick_best(task: str, table: tuple[tuple[str, tuple[str, ...]], ...], default: str) -> tuple[str, int]:
    logger.info("pick_best_enter", extra={"task_length": len(task), "default": default})
    best_name = default
    best_score = 0
    for name, keywords in table:
        score = score_keywords(task, keywords)
        if score > best_score:
            best_name = name
            best_score = score
    logger.info("pick_best_exit", extra={"choice": best_name, "score": best_score})
    return best_name, best_score
