# 🗓️ Yandex Calendar Skill CLI

![CI](https://github.com/Zim-zilim-ai-agent/skill-yandex-calendar/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-target%2095%25-brightgreen)
![Lint](https://img.shields.io/badge/lint-ruff-informational)

Production-grade CalDAV CLI for Yandex Calendar automation.

---

## ✨ Features

- 🔐 Basic auth (username + app password) and OAuth support.
- 📅 Calendar listing and event query by date range.
- 🛠️ Event lifecycle: create / update / delete / search.
- ✅ Todo lifecycle: list / create / complete / delete.
- 🧾 JSON output friendly for scripts and bots.

---

## 🚀 Quick Start

```bash
python3 -m pip install -r requirements.txt
python scripts/yacal.py --username "$YANDEX_CALENDAR_USERNAME" --password "$YANDEX_CALENDAR_PASSWORD" list-calendars
```

Get today's events:

```bash
python scripts/yacal.py --username "$YANDEX_CALENDAR_USERNAME" --password "$YANDEX_CALENDAR_PASSWORD" events --today
```

---

## ⚙️ Configuration

Environment variables:

- `YANDEX_CALENDAR_USERNAME`
- `YANDEX_CALENDAR_PASSWORD`
- `YANDEX_CALENDAR_OAUTH_TOKEN` *(optional)*
- `YANDEX_CALENDAR_USER_ID` *(optional)*

---

## 🧪 Quality Gates

- `ruff check .`
- `pytest -q --cov=scripts/yacal.py --cov-report=term-missing --cov-fail-under=95`

CI runs on push and pull requests.

---

## 📚 Docs

- `SKILL.md` — canonical English skill spec
- `SKILL_ru.MD` — Russian version retained for local usage
- `scripts/yacal.py` — main CLI implementation
- `tests/` — unit tests with mocks
