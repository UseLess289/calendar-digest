# calendar-digest

A self-hosted Docker service that fetches your ICS calendars and sends a formatted daily summary to a Telegram bot every morning.

## Requirements

- Docker + Docker Compose
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram chat ID (get it from `https://api.telegram.org/bot<TOKEN>/getUpdates`) after sending an email to your bot
- ICS URLs for each calendar (secret iCal address from Google Calendar settings, or any ICS feed URL)

## Setup

**1. Clone and configure**

```bash
git clone https://github.com/UseLess289/calendar-digest
cd calendar-digest
```

**2. Create and edit `.env`**

```env
TELEGRAM_TOKEN=123456:ABC-...
TELEGRAM_CHAT_ID=123456789

ICS_DOMICILE=https://calendar.google.com/calendar/ical/XXXXX/private-XXXXX/basic.ics
ICS_TRAVAIL=https://calendar.google.com/calendar/ical/XXXXX/private-XXXXX/basic.ics
ICS_UNIVERSITE=...
```
You should add each ICS_ variable on the table at the top of digest.py.

**3. Build**

```bash
docker compose build
```

**4. Test**

```bash
docker compose run --rm calendar-digest
```

You should receive a Telegram message within seconds.

## Scheduling

Add to your crontab (`crontab -e`) to run every morning at 7am.

If your server is set to UTC, adjust for your timezone (e.g. UTC+2 in summer for Paris):

```
0 5 * * * cd /path/to/calendar-digest && docker compose run --rm calendar-digest
```

## How it works

1. Fetches each configured ICS URL at runtime
2. Expands recurring events (RRULE) for the current day using `recurring-ical-events`
3. Handles both timed events and all-day events, sorted chronologically
4. Formats and sends a digest to your Telegram chat with HTML formatting

## Adding a calendar

**1.** Add the new calendar to `CALENDARS` in `digest.py`:

```python
CALENDARS = {
    ...
    "Sport": os.getenv("ICS_SPORT"),
}
```

**2.** Add its emoji to `CAL_EMOJI`:

```python
CAL_EMOJI = {
    ...
    "Sport": "🏃",
}
```

**3.** Add the variable to `.env`:

```env
ICS_SPORT=https://...
```

Calendars with no URL set in `.env` are silently skipped.
