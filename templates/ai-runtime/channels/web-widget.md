# Web Widget Channel Adapter

## Auth

- Session cookie or short-lived JWT after user login.
- CSRF token on state-changing widget actions.

## Transport

- WebSocket or SSE for streaming responses; REST fallback.
- CORS allowlist for embed origins.

## UX

- Show AI disclosure on first open (manifest `persona.disclosure`).
- Loading, error, and handoff states per shared vocabulary.

## Security

- CSP on embed page; sanitize HTML in user messages.
- Rate limit by session + IP.
