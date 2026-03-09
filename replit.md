# WhatsApp Link Recorder Telegram Bot

A Telegram bot that automatically records WhatsApp group links shared in chats, stores them in a SQLite database, and provides export/delete functionality via inline buttons.

## Architecture

- **main.py** — Single entry point. Runs both the Flask keep-alive server (port 5000, in a background thread) and the Telegram bot polling loop.
- **requirements.txt** — Python dependencies.
- **whatsapp_links.db** — SQLite database (auto-created on first run).

## Features

- Detects WhatsApp group links (`https://chat.whatsapp.com/...`) in messages.
- Deduplicates links in-memory and stores new ones in SQLite.
- Inline buttons: Export all links (grouped by user), delete individual links.
- `/clear` command to wipe all stored links (with confirmation).
- `/help` command with usage instructions.

## Configuration

| Secret | Description |
|--------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather |

## Running

The workflow `Start application` runs `python main.py`, which:
1. Starts Flask on `0.0.0.0:5000` (keep-alive web server, webview output).
2. Starts Telegram bot polling.

## Dependencies

- `python-telegram-bot==20.7`
- `flask>=3.0.0`
- `werkzeug>=3.0.0`
