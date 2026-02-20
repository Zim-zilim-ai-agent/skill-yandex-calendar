---
name: yandex-calendar
description: Manage Yandex Calendar over CalDAV with basic auth or OAuth. Use for listing calendars, querying events by date range, creating/updating/deleting events, and working with VTODO tasks from CLI automation.
---

# Yandex Calendar Skill

Automate Yandex Calendar via CalDAV from the terminal.

## Capabilities

- Authenticate via Basic auth (`username` + app password) or OAuth token.
- List calendars.
- Read events (`--today`, `--from`, `--to`).
- Create, update, delete, search events.
- List, create, complete, delete todos.
- Output JSON for automation pipelines.

## Quick start

```bash
python scripts/yacal.py --username "$YANDEX_CALENDAR_USERNAME" --password "$YANDEX_CALENDAR_PASSWORD" list-calendars
python scripts/yacal.py --username "$YANDEX_CALENDAR_USERNAME" --password "$YANDEX_CALENDAR_PASSWORD" events --today
```

## Environment variables

- `YANDEX_CALENDAR_USERNAME`
- `YANDEX_CALENDAR_PASSWORD`
- `YANDEX_CALENDAR_OAUTH_TOKEN` (optional alternative)
- `YANDEX_CALENDAR_USER_ID` (optional)

## Examples

Create event:

```bash
python scripts/yacal.py --username "$YANDEX_CALENDAR_USERNAME" --password "$YANDEX_CALENDAR_PASSWORD" \
  create --title "Planning" --start "2026-02-25T10:00:00" --end "2026-02-25T11:00:00" --reminder 15
```

Create todo:

```bash
python scripts/yacal.py --username "$YANDEX_CALENDAR_USERNAME" --password "$YANDEX_CALENDAR_PASSWORD" \
  create-todo --title "Send report" --priority 3 --due "2026-02-26T18:00:00"
```
