# skill-yandex-calendar



## Overview

This repository packages the `yandex-calendar` skill as a standalone project with basic quality gates.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

## Structure

- `SKILL.md` — skill metadata and usage instructions
- `scripts/` — executable scripts
- `tests/` — smoke/unit tests

## Security

- Do not commit secrets (.env, credentials, private keys).
- Run local secret scan before pushing.

## Local and remote

If the skill supports remote endpoints, document host setup in `docs/REMOTE_SETUP.md` and provide local fallback options in scripts.
