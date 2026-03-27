---
name: api-versioning-guidance
description: Chooses and applies API versioning strategies (URL path, header, Accept, query), deprecation headers, and coexistence of versions. Use when adding v2, deprecating endpoints, or "how should we version this API."
---

# API Versioning Guidance

## Workflow

1. **Clarify constraints**
   - **Audience:** browser-only, mobile apps (slow upgrades), server-side partners, public internet.
   - **Infrastructure:** single gateway vs multiple deployments; can you route by path or header uniformly?

2. **Pick a version surface**
   - **Path prefix** (e.g. `/v1/`, `/v2/`): highly visible, easy to document and cache; good default for public REST.
   - **Header** (e.g. `API-Version: 2024-01-01` or custom): keeps URLs stable; needs consistent gateway and client discipline.
   - **Accept / content type** (e.g. `application/vnd.company.v2+json`): couples version to representation; useful for hypermedia or strict content negotiation.
   - **Query parameter** (e.g. `?api-version=2`): easy to try in browsers; often messier for caching—use sparingly.

3. **Rules of coexistence**
   - **Old version stays behavior-frozen** except security fixes and clearly documented bugfixes that do not widen/narrow contract unexpectedly.
   - **New work** lands on the latest version; backport only when necessary.
   - Document **sunset**: end date, migration guide, and owner.

4. **Deprecation signaling**
   - **HTTP:** `Deprecation` header (RFC 9745), `Sunset` with HTTP-date, `Link` to migration doc when appropriate.
   - **Spec:** `deprecated: true` on operations and fields; changelog entry.

5. **Implementation sketch**
   - Routing layer dispatches to version-specific handlers or modules; shared domain logic with version-specific DTO mappers reduces duplication.
   - Avoid leaking internal version flags into one mega-handler without boundaries—keeps **check-api-backward-compatibility** reviews tractable.

6. **Governance**
   - Define how many major versions run concurrently (e.g. current + one previous). Plan removal only after metrics show low traffic on old version.

## Notes

- Version **resource** URLs vs **representation** version: REST purists often version representations; many teams version path for simplicity—choose and document.
- Pair with **handle-breaking-change** and **analyze-api-consumer-impact** for migrations.
