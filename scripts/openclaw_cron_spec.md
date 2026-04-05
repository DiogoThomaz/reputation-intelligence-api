# OpenClaw Cron Spec — Daily Review (Telegram)

Schedule: Monday–Friday at 08:00 (America/Sao_Paulo)

Cron expression: `0 8 * * 1-5`

Command (run on OpenClaw host):

```bash
cd /data/.openclaw/workspace/reputation-intelligence-api && python3 scripts/daily_review.py
```

Expected behavior:
- Script prints a Telegram-ready message to stdout.
- Cron wrapper should capture stdout and send to Telegram chat.

Env (optional):
- `TZ=America/Sao_Paulo`
