# How to Use Your Agents

## Quick Reference

All agents are located in `.cursor/agents/` within your project, or in your global `.cursor/agents/` directory, and are available globally.

## Method 1: Chat Interface

Open Cursor chat and reference agents:

```
Act as the code reviewer and review this function
```

```
Use agent.pm.md to break down this feature into tasks
```

```
As the security auditor, check this endpoint for vulnerabilities
```

## Method 2: Composer Mode

In Composer, start with the agent role:

```
As the PM, parse this PDF document and create spec files in specs/
```

```
As the database specialist, optimize this query and add indexes
```

```
As the tester, generate comprehensive tests for this module
```

## Method 3: Project-Specific Rules

Create `.cursorrules` in your project root:

```markdown
# Project Rules

## Code Reviews
Use agent.reviewer.md for all code reviews.

## Security
Use agent.security.md for security audits (HIPAA compliance required).

## Task Planning
Use agent.pm.md for breaking down features into tasks.
```

## Method 4: Direct File Reference

Reference the agent file directly:

```
Review this code following the guidelines in agent.reviewer.md
```

```
Generate tests according to agent.tester.md standards
```

## Common Workflows

### Starting a New Feature
1. **PM Agent**: "As the PM, break down this feature into tasks"
2. **Architect Agent**: "As the architect, review the design approach"
3. **DevOps Agent**: "As DevOps, set up the deployment pipeline"

### Code Review
1. **Reviewer Agent**: "Act as code reviewer, review this PR"
2. **Security Agent**: "As security auditor, check for vulnerabilities"
3. **Tester Agent**: "As tester, verify test coverage"

### Documentation
1. **Docs Agent**: "As documentation writer, update the README"
2. **PM Agent**: "As PM, create API documentation spec"

### Database Work
1. **Database Agent**: "As database specialist, optimize this query"
2. **Architect Agent**: "As architect, review the schema design"

## Agent Combinations

You can use multiple agents in sequence:

```
1. As the PM, break this feature into tasks
2. As the architect, review the technical approach
3. As the security auditor, check for compliance issues
4. As the tester, generate test cases
```

## Tips

- **Be specific**: "Act as the code reviewer" is better than "review this"
- **Reference files**: Mention specific agent files when needed
- **Combine roles**: Use multiple agents for complex tasks
- **Project context**: Create `.cursorrules` for project-specific agent usage

