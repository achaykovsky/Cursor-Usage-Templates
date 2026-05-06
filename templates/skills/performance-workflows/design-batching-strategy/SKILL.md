---
name: design-batching-strategy
description: Designs batching strategies across API, database, queue, and ETL paths with limits, idempotency, and backpressure controls. Use when the user asks about batching, chunking, bulk operations, throughput scaling, or reducing N+1/round trips.
---

# Design Batching Strategy

## Workflow

1. **Define the batching objective**
   - Clarify what should improve: latency, throughput, cost, API quota usage, DB round-trips, or queue pressure.
   - Identify the current unit of work (single record, request, query, event) and target batch unit.

2. **Choose batching boundary**
   - API: request coalescing, bulk endpoints, pagination/windowing.
   - DB: bulk insert/update, batched reads, keyset pagination, avoiding N+1.
   - Queue/stream: consumer batch size, commit/ack boundary, retry unit.
   - ETL: chunk size, partition strategy, checkpoint cadence.
   - Prefer one primary batching boundary first; avoid stacking multiple batching layers in one change.

3. **Set batch policy**
   - Define `max_batch_size`, `max_wait_ms`, and concurrency limit.
   - Include hard caps for memory/timeouts and explicit fallback to smaller batches on failure.
   - Document ordering guarantees and whether partial success is allowed.

4. **Safety and correctness**
   - Require idempotency keys or dedupe semantics for retries.
   - Define transactional boundaries (all-or-nothing vs partial commit).
   - Preserve validation and error visibility; do not hide failed items inside aggregate responses.

5. **Backpressure and degradation**
   - Add rate/concurrency controls to avoid overload.
   - Define degradation path under pressure: reduce batch size, increase wait, or shed non-critical work.

6. **Validation plan**
   - Measure before/after with the same metrics and workload shape.
   - Verify correctness parity (same output, ordering guarantees, failure handling).
   - Add tests for edge cases: empty batch, max batch, partial failure, retry, duplicate input.

## Output Contract

- Recommended batching boundary and rationale.
- Concrete policy values (`max_batch_size`, `max_wait_ms`, concurrency).
- Failure/retry/idempotency behavior.
- Backpressure controls.
- Validation and rollback plan.

## Notes

- Keep policy deterministic and explicit; avoid auto-tuning unless the user asks.
- If data semantics are strict (financial/audit-critical), default to smaller batches and stronger consistency guarantees.
