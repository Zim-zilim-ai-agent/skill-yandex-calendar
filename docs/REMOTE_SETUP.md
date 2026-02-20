# Remote setup for yandex-calendar

## Goal

Document how to run this skill against a remote host.

## Minimal checklist

1. Install Python 3.10+ and ffmpeg on remote host.
2. Install runtime dependencies used by scripts in `scripts/`.
3. Expose service ports if needed (SSH tunnel preferred).
4. Validate with a smoke command and capture logs.

## Docker

Use provided `Dockerfile` for reproducible runtime where applicable.
