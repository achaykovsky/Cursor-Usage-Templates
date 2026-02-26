# AVAILABLE AGENTS

**Subagents** (Settings > Subagents) - In `.cursor/agents/`. Invoke via `@agent(ARCHITECT)`, `// @agent(REVIEWER)` in code.

**Rules** - Technical standards in `.cursor/rules/*.mdc`. Domain-named, apply via globs. Source: `templates/rules/`. Run `.\templates\commands\sync-cursor.ps1` to sync.

| Rule file | Globs / scope |
|-----------|----------------|
| architecture.mdc | `**/*.{py,go,ts,tsx,js,jsx,vue}` |
| security.mdc | alwaysApply |
| python-backend.mdc | `**/*.py` |
| go-backend.mdc | `**/*.go` |
| sql-database.mdc | `**/*.sql`, `**/migrations/**` |
| nosql-database.mdc | `**/models/*.py`, `**/*mongo*`, etc. |
| frontend.mdc | `**/*.{tsx,jsx,vue,css,scss}` |
| devops.mdc | Dockerfile, CI, Terraform |
| documentation.mdc | `**/*.md`, docs |
| planning.mdc | `**/specs/**` |
| code-review.mdc | Code files |
| testing.mdc | Test files |
| performance.mdc | `**/*.{py,go,ts,tsx}` |
| data-pipelines.mdc | `**/dags/**`, `**/pipelines/**` |

## SUBAGENT INVOCATION

| Abbreviation | Subagent Name | Use |
|--------------|---------------|-----|
| PM | PM | `@agent(PM)` |
| Reviewer | REVIEWER | `@agent(REVIEWER)` |
| Tester | TESTER | `@agent(TESTER)` |
| Docs | DOCS | `@agent(DOCS)` |
| Security | SECURITY | `@agent(SECURITY)` |
| Architect | ARCHITECT | `@agent(ARCHITECT)` |
| DevOps | DEVOPS | `@agent(DEVOPS)` |
| DatabaseSQL | DATABASE_SQL | `@agent(DATABASE_SQL)` |
| DatabaseNoSQL | DATABASE_NOSQL | `@agent(DATABASE_NOSQL)` |
| Frontend | FRONTEND | `@agent(FRONTEND)` |
| BackendPython | BACKEND_PYTHON | `@agent(BACKEND_PYTHON)` |
| BackendGo | BACKEND_GO | `@agent(BACKEND_GO)` |
| Performance | PERFORMANCE | `@agent(PERFORMANCE)` |
| DataEngineer | DATA_ENGINEER | `@agent(DATA_ENGINEER)` |

**Global sync**: Copy subagents to `%USERPROFILE%\.cursor\agents\` then run `.\templates\commands\sync-cursor.ps1` in each project.

## AGENT ABBREVIATIONS (Rules)

Use these abbreviations to quickly reference agents:

- **PM** → `agent.pm.md` (Product/Project Manager)
- **Reviewer** → `agent.reviewer.md` (Code Reviewer)
- **Tester** → `agent.tester.md` (Test Generator)
- **Docs** → `agent.docs.md` (Documentation Writer)
- **Security** → `agent.security.md` (Security Auditor)
- **Architect** → `agent.architect.md` (Architecture Advisor)
- **DevOps** → `agent.devops.md` (DevOps Engineer)
- **DatabaseSQL** → `agent.database-sql.md` (SQL Database Specialist)
- **DatabaseNoSQL** → `agent.database-nosql.md` (NoSQL Database Specialist)
- **Frontend** → `agent.frontend.md` (Frontend Expert)
- **BackendPython** → `agent.backend-python.md` (Backend Python Engineer)
- **BackendGo** → `agent.backend-go.md` (Backend Go Engineer)
- **Performance** → `agent.performance.md` (Performance Engineer)
- **DataEngineer** → `agent.data-engineer.md` (Data Engineer)

## CORE AGENTS

### `agent.pm.md` (@PM)
**Product/Project Manager** - Task breakdown, planning, execution
- Break work into atomic, testable tasks
- **Parse input files** (PDF, markdown, text) and generate structured specs
- Generate spec files in `specs/` directory for collaborative planning
- Prioritization, dependency management
- Acceptance criteria, effort estimation
- Sprint/iteration planning

### `agent.reviewer.md` (@Reviewer)
**Code Reviewer** - Quality, maintainability, security, best practices
- Type safety, architecture, security vulnerabilities
- Performance issues, maintainability concerns
- Direct, actionable feedback with severity levels

### `agent.tester.md` (@Tester)
**Test Generator** - Comprehensive test suites, TDD
- Unit, integration, edge case testing
- pytest framework, AAA structure
- Mocking external dependencies

### `agent.docs.md` (@Docs)
**Documentation Writer** - Clear, actionable technical docs
- API docs, README, architecture diagrams
- Code comments (explain "why")
- Scannable format with examples

### `agent.security.md` (@Security)
**Security Auditor** - Vulnerabilities, compliance, data protection
- OWASP Top 10, HIPAA/GDPR compliance
- Input validation, secrets management
- Severity-based reporting

### `agent.architect.md` (@Architect)
**Architecture Advisor** - System design, scalability, patterns
- Scalability strategies, coupling concerns
- Design patterns (when appropriate)
- Tradeoff analysis, migration paths

## SPECIALIZED AGENTS

### `agent.devops.md` (@DevOps)
**DevOps Engineer** - Infrastructure, CI/CD, monitoring
- Docker, CI/CD pipelines, infrastructure as code
- Monitoring, alerting, deployment strategies
- Automation and observability

### `agent.database-sql.md` (@DatabaseSQL)
**SQL Database Specialist** - Relational database design, query optimization
- PostgreSQL, MySQL, SQL Server expertise
- Schema design, normalization, migrations, transactions
- Query optimization, indexing strategies, EXPLAIN plans
- Data integrity and ACID compliance

### `agent.database-nosql.md` (@DatabaseNoSQL)
**NoSQL Database Specialist** - Document, key-value, column-family, graph databases
- MongoDB, DynamoDB, Cassandra, Redis, Neo4j
- Access pattern-driven data modeling
- Partition keys, sharding, eventual consistency
- Denormalization strategies, query optimization

### `agent.frontend.md` (@Frontend)
**Frontend Expert** - Modern web development, UX, performance
- React/TypeScript, component design
- Performance optimization, accessibility
- State management, responsive design

### `agent.backend-python.md` (@BackendPython)
**Backend Python Engineer** - API development, async patterns, database integration
- FastAPI/Django/Flask, async/await, asyncio
- API design (REST, GraphQL), Pydantic validation
- Database integration (SQLAlchemy, asyncpg), background tasks
- Type hints, pytest testing

### `agent.backend-go.md` (@BackendGo)
**Backend Go Engineer** - Concurrent systems, explicit error handling
- Goroutines, channels, context, standard library
- Frameworks (Gin, Echo, Chi), middleware patterns
- Database access (database/sql, GORM), error wrapping
- Table-driven tests, performance optimization

### `agent.performance.md` (@Performance)
**Performance Engineer** - Bottleneck detection, complexity analysis, optimization
- Profiling (CPU, memory, I/O), complexity metrics
- Algorithm optimization, caching strategies
- Load testing, database query optimization
- Metrics and monitoring (latency, throughput)

### `agent.data-engineer.md` (@DataEngineer)
**Data Engineer** - ETL/ELT pipelines, data quality, data infrastructure
- Pipeline design (idempotent, incremental, error handling)
- Data quality validation, schema enforcement, lineage tracking
- Data warehousing (star schemas, dimensional modeling)
- Big data processing (Spark, distributed systems)
- Orchestration (Airflow, Prefect, Dagster)

## USAGE

### In Chat:
- "Act as the code reviewer" or "Use agent.reviewer.md"
- "Act as PM" or "@PM" (uses agent.pm.md)
- "Review this code as a security auditor" or "@Security"
- "Generate tests using agent.tester.md" or "@Tester"

### In `.cursorrules`:
```markdown
# Use code reviewer agent for all PR reviews
See: agent.reviewer.md
# Or use abbreviation
See: @Reviewer
```

### In Composer:
- Mention agent role at start: "As the database specialist, optimize this query..."
- Or use abbreviation: "@DatabaseSQL optimize this query..." or "@DatabaseNoSQL design this data model..."

## COMMON WORKFLOWS

### Starting a New Feature
1. **@PM**: "Break down this feature into tasks"
2. **@Architect**: "Review the design approach"
3. **@DevOps**: "Set up the deployment pipeline"

### Code Review
1. **@Reviewer**: "Review this PR"
2. **@Security**: "Check for vulnerabilities"
3. **@Tester**: "Verify test coverage"

### Documentation
1. **@Docs**: "Update the README"
2. **@PM**: "Create API documentation spec"

### Database Work
1. **@DatabaseSQL**: "Optimize this SQL query"
2. **@DatabaseNoSQL**: "Design this MongoDB schema"
3. **@Architect**: "Review the schema design"

### Backend Development
1. **@BackendPython**: "Implement this API endpoint"
2. **@BackendGo**: "Refactor this handler with proper error handling"
3. **@Performance**: "Profile and optimize this code path"

## BASE CONFIGURATION

All agents inherit from `user.md` (global preferences):
- Senior/Expert level
- Concise, technical, no fluff
- Poetry, pytest, strict typing
- HIPAA/GDPR awareness

## SOURCE

- **Subagents**: `.cursor/agents/` (Settings > Subagents). Source: `templates/agents/subagents/` or `%USERPROFILE%\.cursor\agents\`.
- **Rules**: `.cursor/rules/*.mdc` (proper rules with globs). Source: `templates/rules/`. Run `.\templates\commands\sync-cursor.ps1` to sync.

