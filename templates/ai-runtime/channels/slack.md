# Slack Channel Adapter

## Auth

- Verify `X-Slack-Signature` and timestamp on every request.
- Signing secret from env `SLACK_SIGNING_SECRET` — never in manifest.

## Events

- `app_mention`, `message.im` — map to `conversation_id` = `channel` + `thread_ts` or `ts`.
- Respond within 3s — use `response_url` or async pattern for long LLM calls.

## Output

- Use Slack Block Kit; no raw stack traces in blocks.
- Thread handoff messages for human agents.

## Observability

- Span attribute `channel=slack`; audit `action=message_received|message_sent`.
