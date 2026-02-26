# How to Use Subagents

Subagents are in `.cursor/agents/` and visible in **Settings > Subagents**. Invoke with `@agent(NAME)`.

## Method 1: Chat

```
@agent(REVIEWER) Review this function
```

```
@agent(PM) Break down this feature into tasks
```

```
@agent(SECURITY) Check this endpoint for vulnerabilities
```

## Method 2: Composer

Start with the subagent role:

```
@agent(PM) Parse this PDF and create spec files in specs/
```

```
@agent(DATABASE_SQL) Optimize this query and add indexes
```

```
@agent(TESTER) Generate tests for this module
```

## Method 3: Code Comments

In code, use `// @agent(NAME)` to delegate:

```python
# @agent(REVIEWER) - Review this auth logic
def authenticate(user_id: str, token: str) -> bool:
    ...
```

```go
// @agent(BACKEND_GO) - Add proper error handling
func (s *Service) GetUser(ctx context.Context, id string) (*User, error) {
```

## Method 4: Project Rules

In `.cursorrules` or rules, reference subagents:

```markdown
# Code Reviews
Use @agent(REVIEWER) for all PR reviews.

# Security
Use @agent(SECURITY) for security audits.
```

## Common Workflows

### Starting a New Feature
1. `@agent(PM)` Break down this feature into tasks
2. `@agent(ARCHITECT)` Review the design approach
3. `@agent(DEVOPS)` Set up the deployment pipeline

### Code Review
1. `@agent(REVIEWER)` Review this PR
2. `@agent(SECURITY)` Check for vulnerabilities
3. `@agent(TESTER)` Verify test coverage

### Documentation
1. `@agent(DOCS)` Update the README
2. `@agent(PM)` Create API documentation spec

### Database Work
1. `@agent(DATABASE_SQL)` Optimize this SQL query
2. `@agent(DATABASE_NOSQL)` Design this MongoDB schema
3. `@agent(ARCHITECT)` Review the schema design

### Backend Development
1. `@agent(BACKEND_PYTHON)` Implement this API endpoint
2. `@agent(BACKEND_GO)` Refactor this handler with proper error handling
3. `@agent(PERFORMANCE)` Profile and optimize this code path

## Chaining Subagents

Use multiple subagents in sequence:

```
1. @agent(PM) Break this feature into tasks
2. @agent(ARCHITECT) Review the technical approach
3. @agent(SECURITY) Check for compliance issues
4. @agent(TESTER) Generate test cases
```

## Tips

- **Be specific**: "@agent(REVIEWER) Review this auth function for SQL injection" is better than "review this"
- **Subagent + Rules**: Subagents provide role/prompt; rules (`.cursor/rules/*.mdc`) add technical standards when editing matching files
- **Sync**: Run `.\templates\commands\sync-cursor.ps1` to update `.cursor/agents/` and `.cursor/rules/`
