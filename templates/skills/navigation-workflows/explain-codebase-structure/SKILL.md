---
name: explain-codebase-structure
description: Maps key directories, entry points, and data flow; answers "where does X happen," "how does Y work," and points to relevant files. Use when the user is new to the repo, asks "explain the codebase," or "where is X."
---

# Explain Codebase Structure

## Workflow

1. **Clarify the question**
   - What does the user need? (Overview of the repo, location of a feature, or how a flow works.) Identify key terms (e.g. "auth," "payment," "API entry").

2. **Map the structure**
   - **Directories:** List top-level and important subdirs (e.g. `src/`, `api/`, `tests/`). Note the role of each (e.g. "handlers," "domain," "db").
   - **Entry points:** Main binary, server startup, CLI commands, or public API surface. How does a request or command reach the code?
   - **Data flow (high level only):** For "how does X work," one-line input → layer → output with file/module names. For step-by-step tracing, use **trace-data-flow** (navigation-workflows).

3. **Point to files**
   - Name the files or modules that implement the asked-about behavior. Give paths and one-line descriptions. If the user asked "where is X," lead with that file and then context.

4. **Summarize**
   - Short narrative: purpose of the repo or subsystem, then the answer to the user's question. Keep it scannable (bullets or short paragraphs).

## Routing boundaries

- **explain-codebase-structure** — repo map, entry points, where X lives, one-paragraph how-it-works.
- **trace-data-flow** — step-by-step path for one input/value through handlers, services, and persistence.
- **organize-project-structure** — assess layout issues and plan or execute folder moves; not for explaining or tracing.

## Notes

- Infer structure from the repo; do not assume a framework. Use README or docs if they exist, but verify against the code.
- If the codebase is large, focus on the area that answers the question; mention other areas briefly.
