# Jerkgram Notifications Backend PoC

**Test accounts only. Do not connect a main Telegram account.**

This directory is the temporary backend proof of concept for Jerkgram rich notifications. It creates a separate Telegram MTProto authorization with Telegram's login-token flow. It never copies the iOS Jerkgram session.

## What works in this milestone

- `GET /health`
- `POST /pair/start` — creates a short-lived Telegram login token and returns a `jerkgram://push/authorize?...` URL
- `GET /pair/{pair_id}` — reports `pending`, `approved`, `expired`, or `failed`
- Telethon keeps the approved test session connected in memory only
- no message bodies or Telegram session strings are written to disk/logs

The currently installed Build138 should **not** be assumed to accept the new `jerkgram://push/authorize` route yet. The native patch/build comes only after this backend is verified.

## iPhone + GitHub Codespaces

1. In GitHub, create two Codespaces secrets named `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` using the Jerkgram Telegram application credentials. Never commit the API hash.
2. Create a Codespace for branch `dev/notifications-backend-poc` and choose the **Jerkgram Notifications Backend PoC** dev-container configuration if GitHub asks.
3. In the Codespaces terminal run:

```bash
cd notifications-backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Open forwarded port 8000 and visit `/docs`. `GET /health` should show `telegram_configured: true`.
5. Use `POST /pair/start` only with a disposable/test Telegram account once the matching native acceptance handler is ready.

Codespaces is only a development laboratory. It is not the production host for user Telegram sessions.

## Local test command used by CI

```bash
python -m pip install -e '.[test]'
pytest -q
```

## Security boundary

An approved backend session has normal Telegram-account session power. It is not server-enforced to notifications. Before any wider test, the project needs encrypted persistent session storage with separated key management, explicit disconnect/revoke, an incident-response plan, and privacy/legal review.
