# AVAILABLE AGENTS

**Global agents** - Available in ALL projects.

Agents are stored globally at `C:\Users\annac\.cursor\` and copied to `.cursor/rules/` in this project.

## AGENT ABBREVIATIONS

Use these abbreviations to quickly reference agents:

- **PM** → `agent.pm.md` (Product/Project Manager)
- **Reviewer** → `agent.reviewer.md` (Code Reviewer)
- **Tester** → `agent.tester.md` (Test Generator)
- **Docs** → `agent.docs.md` (Documentation Writer)
- **Security** → `agent.security.md` (Security Auditor)
- **Architect** → `agent.architect.md` (Architecture Advisor)
- **DevOps** → `agent.devops.md` (DevOps Engineer)
- **Database** → `agent.database.md` (Database Specialist)
- **Frontend** → `agent.frontend.md` (Frontend Expert)
- **BackendPython** → `agent.backend-python.md` (Backend Python Engineer)
- **BackendGo** → `agent.backend-go.md` (Backend Go Engineer)
- **Performance** → `agent.performance.md` (Performance Engineer)

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

### `agent.database.md` (@Database)
**Database Specialist** - Schema design, query optimization
- PostgreSQL expertise, migrations, transactions
- Query optimization, indexing strategies
- Data integrity and ACID compliance

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
- Or use abbreviation: "@Database optimize this query..."

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
1. **@Database**: "Optimize this query"
2. **@Architect**: "Review the schema design"

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

All agents (including this file) are stored globally at: `C:\Users\annac\.cursor\`

**To update agents**: Edit the global files in `C:\Users\annac\.cursor\`, then run `.\sync-agents.ps1` in each project to sync local copies.

