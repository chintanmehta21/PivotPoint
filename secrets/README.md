# Secrets

This folder stores sensitive credentials. **Never commit actual secret files.**

## Expected files (create from templates):

### Fyers API (primary market data source)
- `fyers_credentials.json` — app_id, secret_key, access_token

### Discord
- `discord_credentials.json` — bot_token, channel_id

### Telegram
- `telegram_credentials.json` — bot_token, chat_id

## Template

Each credentials file should follow this JSON structure:

```json
{
  "key": "value"
}
```
