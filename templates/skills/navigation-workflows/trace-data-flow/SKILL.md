---
name: trace-data-flow
description: Follows data from input to output (or error) through the codebase; documents the path and transformations. Use when the user asks to "trace this request," "where does this value come from," or "follow this flow."
---

# Trace Data Flow

## Workflow

1. **Define start and end**
   - Where does the flow start? (e.g. HTTP request, CLI arg, event, file.) What is the input (payload, key, or path)?
   - Where should we trace to? (e.g. response, DB write, log, or specific function.) If the user said "trace this request," end at response or persistence.

2. **Follow the path**
   - From the entry point: which function or handler receives the input? Then which layer (e.g. service, repository) and in what order?
   - Note transformations: parsing, validation, mapping, or business logic that changes the data. Note branches (e.g. error path vs success path).
   - Continue until the end point. List file paths and function names (or key lines) so the user can open the code.

3. **Document**
   - Produce a short trace: Entry → Step 1 → Step 2 → … → Exit. For each step: file/module, function or class, and what happens to the data.
   - If the flow diverges (e.g. async or multiple consumers), describe the main path first and note branches.

4. **Summarize**
   - One-paragraph summary of the flow. Call out any side effects (e.g. DB write, external call) or non-obvious behavior.

## Notes

- Stay at a level that is useful: not every variable assignment, but each logical step. Increase detail only where the user needs it.
- If the path is unclear (e.g. dynamic dispatch), describe what you can infer and where the trail stops.
