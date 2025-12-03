# Cursor Usage Templates

Centralized Markdown templates for defining Cursor instructions at multiple scopes, plus specialized agent roles for different tasks.

## Quick Start

1. **Copy base templates** into your Cursor instructions panel:
   - `templates/workspace.md` – baseline rules for the entire workspace
   - `templates/project.md` – project-specific objectives and constraints
   - `templates/user.md` – personal preferences for individual collaborators

2. **Use agents** in Chat or Composer:
   ```
   Act as the code reviewer and review this function
   ```
   ```
   As the PM, break down this feature into tasks
   ```

3. **Replace placeholders** in templates with concrete details.

4. **Keep templates under version control** so the team can iterate together.

## Template Scopes

### Base Templates

- **`templates/workspace.md`** – Organization-wide rules, tooling, automation, testing policy
- **`templates/project.md`** – Project-specific standards, architecture patterns, constraints
- **`templates/user.md`** – Personal coding style, tool preferences, global principles

These templates intentionally avoid language- or framework-specific guidance; add technical details only when a project demands them.

## Agent System

Specialized agent roles stored in `templates/agents/` for focused tasks.

### Available Agents

| Agent | Abbreviation | Purpose |
|-------|-------------|---------|
| `agent.pm.md` | @PM | Task breakdown, planning, spec generation |
| `agent.reviewer.md` | @Reviewer | Code quality, maintainability, best practices |
| `agent.tester.md` | @Tester | Test generation, TDD, pytest suites |
| `agent.docs.md` | @Docs | API docs, README, architecture diagrams |
| `agent.security.md` | @Security | Vulnerabilities, compliance, data protection |
| `agent.architect.md` | @Architect | System design, scalability, patterns |
| `agent.devops.md` | @DevOps | Infrastructure, CI/CD, monitoring |
| `agent.database.md` | @Database | Schema design, query optimization |
| `agent.frontend.md` | @Frontend | React/TypeScript, UX, performance |

See `templates/agents/AGENTS.md` for full agent descriptions.

### Using Agents

**In Chat:**
```
Act as the code reviewer
Use agent.pm.md to break down this feature
@Security check this endpoint for vulnerabilities
```

**In Composer:**
```
As the PM, parse this PDF and create spec files in specs/
As the database specialist, optimize this query
```

**In `.cursorrules`:**
```markdown
# Use code reviewer agent for all PR reviews
See: agent.reviewer.md
```

**Direct file reference:**
```
Review this code following agent.reviewer.md guidelines
```

### Common Workflows

**Starting a new feature:**
1. `@PM` – Break down into tasks
2. `@Architect` – Review design approach
3. `@DevOps` – Set up deployment pipeline

**Code review:**
1. `@Reviewer` – Review PR
2. `@Security` – Check vulnerabilities
3. `@Tester` – Verify test coverage

**Documentation:**
1. `@Docs` – Update README
2. `@PM` – Create API documentation spec

See `templates/agents/AGENTS_USAGE.md` for detailed usage examples.

## Project Structure

```
templates/
├── workspace.md          # Organization-wide rules
├── project.md            # Project-specific config
├── user.md               # Personal preferences
└── agents/               # Specialized agent roles
    ├── AGENTS.md         # Agent overview and descriptions
    ├── AGENTS_USAGE.md   # Usage guide with examples
    ├── agent.pm.md       # Product/Project Manager
    ├── agent.reviewer.md # Code Reviewer
    ├── agent.tester.md   # Test Generator
    ├── agent.docs.md     # Documentation Writer
    ├── agent.security.md # Security Auditor
    ├── agent.architect.md # Architecture Advisor
    ├── agent.devops.md   # DevOps Engineer
    ├── agent.database.md # Database Specialist
    └── agent.frontend.md # Frontend Expert
```

## Troubleshooting

**Agents not recognized:**
- Reference agents by full filename: `agent.reviewer.md`
- Or use abbreviations: `@Reviewer`
- Ensure agent files exist in `templates/agents/`

**Template conflicts:**
- `user.md` sets global preferences (applies to all projects)
- `project.md` extends global rules (project-specific only)
- `workspace.md` defines organization-wide standards

**Agent inheritance:**
- All agents inherit from `user.md` (global preferences)
- Agents can be referenced in `project.md` for project-specific usage
