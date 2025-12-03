# AVAILABLE AGENTS

Global role-based agents for Cursor. Reference these in chat or `.cursorrules`.

## CORE AGENTS

### `agent.reviewer.md`
**Code Reviewer** - Quality, maintainability, security, best practices
- Type safety, architecture, security vulnerabilities
- Performance issues, maintainability concerns
- Direct, actionable feedback with severity levels

### `agent.tester.md`
**Test Generator** - Comprehensive test suites, TDD
- Unit, integration, edge case testing
- pytest framework, AAA structure
- Mocking external dependencies

### `agent.docs.md`
**Documentation Writer** - Clear, actionable technical docs
- API docs, README, architecture diagrams
- Code comments (explain "why")
- Scannable format with examples

### `agent.security.md`
**Security Auditor** - Vulnerabilities, compliance, data protection
- OWASP Top 10, HIPAA/GDPR compliance
- Input validation, secrets management
- Severity-based reporting

### `agent.architect.md`
**Architecture Advisor** - System design, scalability, patterns
- Scalability strategies, coupling concerns
- Design patterns (when appropriate)
- Tradeoff analysis, migration paths

### `agent.pm.md`
**Product/Project Manager** - Task breakdown, planning, execution
- Break work into atomic, testable tasks
- **Parse input files** (PDF, markdown, text) and generate structured specs
- Generate spec files in `specs/` directory for collaborative planning
- Prioritization, dependency management
- Acceptance criteria, effort estimation
- Sprint/iteration planning

## SPECIALIZED AGENTS

### `agent.devops.md`
**DevOps Engineer** - Infrastructure, CI/CD, monitoring
- Docker, CI/CD pipelines, infrastructure as code
- Monitoring, alerting, deployment strategies
- Automation and observability

### `agent.database.md`
**Database Specialist** - Schema design, query optimization
- PostgreSQL expertise, migrations, transactions
- Query optimization, indexing strategies
- Data integrity and ACID compliance

### `agent.frontend.md`
**Frontend Expert** - Modern web development, UX, performance
- React/TypeScript, component design
- Performance optimization, accessibility
- State management, responsive design

## USAGE

**In Chat:**
- "Act as the code reviewer" or "Use agent.reviewer.md"
- "Review this code as a security auditor"
- "Generate tests using agent.tester.md"

**In `.cursorrules`:**
```markdown
# Use code reviewer agent for all PR reviews
See: agent.reviewer.md
```

**In Composer:**
- Mention agent role at start: "As the database specialist, optimize this query..."

## BASE CONFIGURATION

All agents inherit from `user.md` (global preferences):
- Senior/Expert level
- Concise, technical, no fluff
- Poetry, pytest, strict typing
- HIPAA/GDPR awareness

