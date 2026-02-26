# AVAILABLE SUBAGENTS

Subagents live in `.cursor/agents/` and appear in **Settings > Subagents**. Invoke via `@agent(NAME)` in chat or `// @agent(NAME)` in code comments.

**Short names** (for invocation) vs **file names** (descriptive). Models chosen for cost vs quality: Opus only for critical reasoning (SECURITY, ARCHITECT); Sonnet for structured analysis; Composer for code-heavy tasks.

| Invoke | File | Model |
|--------|------|-------|
| PM | product_manager.md | claude-4.6-sonnet |
| REVIEWER | code_reviewer.md | claude-4.6-sonnet |
| TESTER | test_engineer.md | composer-1.5 |
| DOCS | documentation_writer.md | composer-1.5 |
| SECURITY | security_engineer.md | claude-4.6-opus |
| ARCHITECT | architecture_advisor.md | claude-4.6-opus |
| DEVOPS | devops_engineer.md | composer-1.5 |
| DATABASE_SQL | sql_database_engineer.md | composer-1.5 |
| DATABASE_NOSQL | nosql_database_engineer.md | composer-1.5 |
| FRONTEND | frontend_engineer.md | composer-1.5 |
| BACKEND_PYTHON | backend_python_engineer.md | composer-1.5 |
| BACKEND_GO | backend_go_engineer.md | composer-1.5 |
| PERFORMANCE | performance_engineer.md | claude-4.6-sonnet |
| DATA_ENGINEER | data_engineer.md | composer-1.5 |

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

### FRONTEND (frontend_engineer.md)
React/TypeScript, UX, accessibility, performance. Component design, Core Web Vitals.

### BACKEND_PYTHON (backend_python_engineer.md)
FastAPI/Django, async, Pydantic, SQLAlchemy. Security-first, type hints, pytest.

### BACKEND_GO (backend_go_engineer.md)
Gin/Echo, GORM, idiomatic Go. Error handling, table-driven tests, benchmarks.

### PERFORMANCE (performance_engineer.md)
Profiling, bottlenecks, complexity. Measure before optimize. Database, API, caching.

### DATA_ENGINEER (data_engineer.md)
ETL/ELT, pipelines, data quality. Idempotent, incremental, Airflow/Prefect/Dagster.

## RULES (TECHNICAL STANDARDS)

Rules in `.cursor/rules/*.mdc` add technical depth and apply via globs. Source: `templates/rules/`.

| Rule | Scope |
|------|-------|
| architecture.mdc | Code files |
| security.mdc | alwaysApply |
| python-backend.mdc | `**/*.py` |
| go-backend.mdc | `**/*.go` |
| sql-database.mdc | SQL, migrations |
| nosql-database.mdc | NoSQL models |
| frontend.mdc | TSX, Vue, CSS |
| devops.mdc | Dockerfile, CI, Terraform |
| documentation.mdc | Markdown, docs |
| planning.mdc | `**/specs/**` |
| code-review.mdc | Code files |
| testing.mdc | Test files |
| performance.mdc | Code files |
| data-pipelines.mdc | DAGs, pipelines |

## SYNC

Run `.\templates\commands\sync-cursor.ps1` to copy subagents from `templates/agents/subagents/` (or `%USERPROFILE%\.cursor\agents\`) to `.cursor/agents/` and rules to `.cursor/rules/`. The sync clears `.cursor/agents/` before copying so renamed files don't persist.
