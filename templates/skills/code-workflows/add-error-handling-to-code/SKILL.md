---
name: add-error-handling-to-code
description: Adds specific raises, narrow catches, exception chaining, and domain error types when writing or editing code. Use when the user asks to "add error handling," "raise specific exceptions," "custom exceptions," or when shipping new or materially changed logic with raise/except paths per ai-guardrails.
---

# Add Error Handling to Code

## Workflow

0. **Discover existing capability** — Run **discover-before-implement** (shared-practices). Check existing domain error types and handlers.

1. **Choose specific types**
   - **Python:** Prefer stdlib types that match the failure (`ValueError`, `TypeError`, `FileNotFoundError`) or a small domain hierarchy (`UserNotFoundError`, `PaymentDeclinedError`). Avoid bare `Exception("failed")` unless re-wrapping at a true boundary.
   - **Go:** Return sentinel or typed errors (`var ErrNotFound = errors.New("not found")`, custom struct with `Error() string`). Wrap with context via `fmt.Errorf("load user %q: %w", id, err)` — never drop the cause.
   - **TS/JS:** Prefer typed errors / discriminated result types over generic `throw new Error("failed")` when callers branch on failure kind.

2. **Catch narrowly; handle at boundaries**
   - Catch only exceptions/errors you can recover from or translate. At HTTP/CLI/worker boundaries, map domain failures to contract-safe responses — do not expose stack traces or internal types (see `api-contract.mdc`).
   - **Python anti-pattern:** `except Exception:` in business logic. Reserve broad handlers for top-level middleware with logging + safe fallback.
   - **Go:** Check with `errors.Is` / `errors.As`; do not compare wrapped errors with `==` alone.

3. **Preserve cause chains**
   - **Python:** `raise DomainError("...") from exc` when translating; never bare `raise DomainError(...)` after `except` if the original cause matters for debugging.
   - **Go:** Always `%w` when the caller may need `errors.Is`/`errors.As`.

4. **Keep domain errors small**
   - One module or package owns related types. Subclass/message should tell callers *what failed* and *why retry might help* (transient vs permanent).
   - Add a one-line doc comment on exported/domain error types explaining when they are raised.

5. **Test failure contracts**
   - **Python:** `pytest.raises(SpecificError, match="...")` for each new failure path — not only generic assert on message.
   - **Go:** Table-driven tests with `errors.Is(want, got)` or type assertions via `errors.As`.

6. **Pair with logging at boundaries**
   - Log once at the boundary where you translate or give up — include error type and safe context. Apply **add-logging-to-code** (code-workflows). Do not log-and-rethrow the same failure at every layer.

## Anti-patterns

- **Generic raise/catch:** `raise Exception(...)` / `except Exception: pass`.
- **Swallowing errors:** Empty except blocks, ignored `_` err in Go, catch without log or re-raise at boundaries.
- **Leaking internals:** Returning raw `str(exc)` or stack traces to API clients.
- **Stringly typed errors:** Comparing `err.Error() == "not found"` instead of typed/sentinel checks.

## Notes

- Policy baseline: `python-backend.mdc`, `go-backend.mdc`, and `ai-guardrails.mdc`.
- For inline rationale on non-obvious error mapping — use **add-comments-to-code** (code-workflows).
- For structured logs on error paths — use **add-logging-to-code** (code-workflows).
