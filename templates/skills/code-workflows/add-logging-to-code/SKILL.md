---
name: add-logging-to-code
description: Adds structured logging to code paths (entry/exit, errors, key decisions); applies log levels, follows project patterns, and redacts sensitive data. Use when the user asks to "add logging," "log this," "instrument with logs," or "make this debuggable."
---

# Add Logging to Code

## Workflow

1. **Identify log points**
   - **Entry:** Log function/handler entry with key identifiers (request_id, correlation_id if present) and non-sensitive inputs.
   - **Exit:** Log success with outcome or result summary (no full payloads).
   - **Errors:** Log at ERROR with exception type, message, and context. No stack traces in production logs unless configured.
   - **Decisions:** Log INFO when branching on business logic (e.g. cache hit/miss, fallback chosen).

2. **Choose log level**
   - **DEBUG:** Verbose, development-only (e.g. intermediate values, loop iterations).
   - **INFO:** Normal flow (entry, exit, key milestones).
   - **WARN:** Recoverable issues (retries, fallbacks, deprecated path used).
   - **ERROR:** Failures requiring attention (exceptions, failed validations).

3. **Use structured logging**
   - Prefer key-value fields over string concatenation.
   - Python: `logger.info("request_completed", extra={"request_id": rid, "status": status, "duration_ms": d})`
   - Go: `log.Info("request completed", "request_id", rid, "status", status, "duration_ms", d)`
   - JS/TS: `logger.info({ requestId: rid, status, durationMs: d }, "request completed")`

4. **Redact sensitive data**
   - Apply **redact-sensitive-in-output** (shared-practices). Never log passwords, tokens, PII, or full request/response bodies with secrets.
   - Use placeholders: `user_id`, `REDACTED`, or hash/prefix only.

5. **Follow project patterns**
   - Use existing logger (e.g. `structlog`, `logrus`, `winston`).
   - Match log format, level naming, and where logs are written.
   - Add correlation/request IDs if the project uses them.

## Anti-patterns

- **Noisy logs:** Avoid DEBUG in hot paths or high-frequency loops.
- **String interpolation:** Prefer structured fields for filtering and parsing.
- **Logging in libraries:** Only log at WARN/ERROR unless the library explicitly supports configurable verbosity.
- **Secrets in logs:** Never log raw credentials, tokens, or full PII.

## Notes

- For broader observability (metrics, traces), use **add-observability-for-debugging** (performance-workflows).
- Document what was added: "Search logs for `request_id=X` to trace this flow."
