---
name: sensitive-data-handling
description: Identifies PII or regulated data in code paths, ensures no logging or response leakage, and suggests redaction, tokenization, or policy alignment (e.g. HIPAA, GDPR). Use when the user works with user/patient data, auth, or mentions compliance.
---

# Sensitive Data Handling

## Workflow

1. **Identify sensitive data**
   - From the code or user description: where does PII or regulated data flow? (e.g. names, emails, health data, payment info, session tokens.)
   - Trace: input, storage, processing, and output (responses, logs, exports, queues).

2. **Check for leakage**
   - **Logs:** Sensitive fields logged in plain text? Suggest redaction (e.g. mask, hash, or omit). Ensure stack traces and errors do not include PII.
   - **Responses:** APIs or UI returning more than necessary? Suggest minimal exposure and consistent masking in serialization.
   - **Storage:** Plain text where encryption or tokenization is expected? Note and suggest alignment with policy.
   - **Third parties:** Data sent to external services; ensure contracts and consent are respected.

3. **Suggest improvements**
   - Redaction patterns: what to mask (e.g. last 4 digits only), and where (logs, responses, analytics).
   - Tokenization: replace raw values with tokens for internal use where appropriate.
   - Policy: reference HIPAA, GDPR, or project policy; suggest access control, retention, and audit logging if relevant.

4. **Summarize**
   - List data types and locations reviewed, findings (leakage or risk), and top recommendations. Do not paste sensitive data in the summary.

## Notes

- Treat all user/patient identifiers and auth material as sensitive. When in doubt, recommend redaction or minimal exposure.
- Apply **redact-sensitive-in-output** (shared-practices) in all suggestions and summaries.
