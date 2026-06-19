# PROJECT-SPECIFIC RULES

Project-specific configuration that complements global `user.md` and `AGENTS.md`.

**Note**: This file extends global rules. Do not duplicate or override global standards.

## PROJECT CONTEXT
- **Name**: 
- **Tech Stack**: 
- **Primary Language(s)**: 
- **Framework(s)**: 

## PROJECT-SPECIFIC STANDARDS

### Code Organization
- Directory structure conventions:
- Module/package naming patterns:
- File naming conventions:

### Architecture Patterns
- Preferred design patterns for this project:
- Domain-specific conventions:
- Integration patterns:

### Dependencies & Tools
- Project-specific tooling (beyond global `poetry`/`pytest`):
- Required external services:
- Environment setup notes:

## AGENT USAGE

See [`.cursor/USAGE.md`](.cursor/USAGE.md) after sync, or [`templates/USAGE.md`](USAGE.md) in the templates repo. Preferred agents for this project (full list: `agents/AGENTS.md` in `.cursor/`):
- Primary: 
- Secondary: 

Example: `@agent(REVIEWER)` for all PRs, `@agent(DATABASE_SQL)` for SQL schema changes, `@agent(DATABASE_NOSQL)` for NoSQL data modeling

## PROJECT CONSTRAINTS

### Technical Constraints
- Performance requirements:
- Scalability considerations:
- Integration limitations:

### Compliance & Security
- Project-specific compliance needs (beyond global HIPAA/GDPR):
- Security requirements:
- Data handling rules:

## WORKFLOW NOTES
- Project-specific development steps:
- Testing approach (extends global pytest standards):
- Review process:

## REFERENCES
- Related documentation:
- Architecture diagrams:
- External specs:
