---
name: analyze-api-consumer-impact
description: Identifies who consumes an API and what breaks for them (internal apps, SDKs, partners); summarizes blast radius and migration work. Use when changing or removing endpoints, tightening schemas, or "who will this break."
---

# Analyze API Consumer Impact

## Workflow

1. **Define the change**
   - Precisely list endpoints, fields, status codes, or behaviors changing (link to OpenAPI diff or ticket).

2. **Discover consumers (layered)**
   - **Same repo:** search for path strings, client wrappers, OpenAPI-generated clients, integration tests, and fixtures.
   - **Org:** internal package registries, shared SDK repos, API gateways routing to the service, feature flags calling the API.
   - **External:** documented partner integrations, public SDKs, webhook subscribers, or unknown clients—infer from **analytics** (per-route traffic by key, User-Agent, API key tenant) if available.

3. **Per consumer profile**
   - **Who** (team, product, internal vs external).
   - **How they integrate** (generated client version, raw fetch, batch jobs, mobile store review delays).
   - **What breaks** (compile-time, runtime parse errors, logical assumptions like "404 never happens").
   - **Effort to migrate** (one-line vs weeks); **blockers** (LTS mobile, regulated change windows).

4. **Blast radius summary**
   - **Critical path:** revenue, auth, or safety-critical callers—flag first.
   - **Counts:** approximate teams or apps affected; unknown share of traffic (risk).

5. **Recommendations**
   - Timeline: parallel run, feature flags, **deprecation period** (see **api-versioning-guidance**).
   - Comms: changelog, direct partner notice, developer blog or status page for externals.
   - Pair with **handle-breaking-change** for deprecation vs adapter vs new version.

## Notes

- Do not assume "no repo references" means no consumers—check gateway logs and product owners.
- Redact tenant names and PII in shared reports (**redact-sensitive-in-output**).
