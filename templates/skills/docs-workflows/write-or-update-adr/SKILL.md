---
name: write-or-update-adr
description: Drafts or updates an Architecture Decision Record: context, decision, consequences, and status; places it in project convention (e.g. docs/adr/). Use when the user describes a design choice, asks to "document this decision," or "write an ADR."
---

# Write or Update ADR

## Workflow

1. **Capture context**
   - What decision was made? What problem or constraint led to it? What options were considered?
   - Gather from the user or from recent code/PRs: technology choice, structure, or process (e.g. "we use X because Y").

2. **Draft the ADR**
   - **Title:** Short, imperative (e.g. "Use PostgreSQL for primary store").
   - **Status:** Proposed, Accepted, Deprecated, or Superseded. If superseded, link to the new ADR.
   - **Context:** Why the decision was needed; key constraints and forces.
   - **Decision:** What was decided; main points.
   - **Consequences:** Positive and negative outcomes; tradeoffs. Call out follow-up work or reversibility.

3. **Place in project**
   - Use the project's convention (e.g. `docs/adr/`, `doc/architecture/`). Number or date if the project does (e.g. `0001-use-postgresql.md`). Link from a main index if one exists.

4. **Update existing ADR**
   - If updating: add a short "Updates" or "Changelog" section, or append to consequences. If the decision is superseded, set status and link to the new ADR.

## Notes

- Keep the ADR concise; avoid restating general knowledge. Focus on the specific decision and its rationale.
- Use consistent formatting (e.g. same headers, status values) as other ADRs in the repo.
