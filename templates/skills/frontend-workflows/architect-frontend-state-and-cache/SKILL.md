---
name: architect-frontend-state-and-cache
description: Designs frontend state boundaries and caching strategy (local state vs server state, query keys, invalidation, optimistic updates). Use when implementing or fixing React Query/SWR/store behavior, stale data issues, or race conditions.
---

# Architect Frontend State and Cache

## Workflow

1. **Partition state responsibilities**
   - Separate local UI state, derived state, and server state.
   - Remove duplicated state where derivation is reliable.

2. **Define fetch/cache contracts**
   - Standardize query keys and input normalization.
   - Set staleTime/gcTime (cacheTime in older React Query versions)/retry policy based on data volatility and UX needs.

3. **Design mutation behavior**
   - Define optimistic update scope, rollback logic, and conflict handling.
   - Explicitly define invalidation and refetch triggers after writes.

4. **Handle concurrency and failure**
   - Identify race conditions (rapid navigation, double-submit, overlapping mutations).
   - Specify cancellation, deduplication, and idempotency expectations.

5. **Lock in predictable UI states**
   - Ensure consumers expose loading/empty/error/success consistently.
   - Keep API adapter boundaries typed and explicit.

## Output Contract

- State boundary map
- Query key + invalidation strategy
- Mutation/optimistic update policy
- Failure and race-condition handling notes

## Shared Routing

For cross-skill routing and FE-vs-generic escalation, follow `orchestrate-frontend-delivery`.
