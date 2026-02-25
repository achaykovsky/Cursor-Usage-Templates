---
name: add-observability-for-debugging
description: Identifies what to instrument (logs, metrics, traces) for a feature or failure mode; adds minimal instrumentation and documents how to use it. Use when the user asks to "add logging," "how do I debug this in prod," or "instrument this."
---

# Add Observability for Debugging

## Workflow

1. **Identify the target**
   - What needs to be observable? (e.g. a new feature, a flaky path, or a production failure mode.)
   - Define: which operations, inputs, and outcomes matter (success, failure, latency, count).

2. **Choose instrumentation**
   - **Logs:** Structured log lines at key points (entry, exit, errors). Include correlation ID or request ID if the project uses it. Apply **redact-sensitive-in-output** (shared-practices).
   - **Metrics:** Counters or histograms for rates, latency, or errors if the project has a metrics system. Use existing naming and labels.
   - **Traces:** If the project uses distributed tracing, add spans for the operation. Keep span names and attributes consistent.

3. **Add minimally**
   - Add only what is needed to debug or monitor the target. Avoid noisy logs or high-cardinality metrics that could overwhelm storage or dashboards.
   - Follow project patterns: log level, format, and where logs go; metric names and tags.

4. **Document usage**
   - Short note: what was added, where, and how to use it (e.g. "Search logs for `request_id=X` to follow this request;" or "Dashboard Y shows latency for this path").

## Notes

- Apply **redact-sensitive-in-output** (shared-practices) for logs, metrics, and traces.
- If the project has no existing observability stack, suggest minimal logging first and note that metrics/tracing may require infrastructure.
