#!/bin/bash
# Wrapper script for Yandex Calendar CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${SCRIPT_DIR}/.venv/bin/python"
MAIN_SCRIPT="${SCRIPT_DIR}/scripts/yacal.py"

# Activate virtual environment if exists
if [[ -f "${VENV_PYTHON}" ]]; then
    PYTHON="${VENV_PYTHON}"
else
    PYTHON="python3"
fi

# Check if dependencies are installed
if [[ ! -f "${SCRIPT_DIR}/.venv/bin/activate" ]]; then
    echo "Setting up virtual environment..."
    cd "${SCRIPT_DIR}"
    uv venv .venv
    .venv/bin/pip install caldav || {
        echo "Failed to install caldav. Trying with uv..."
        uv pip install --python .venv/bin/python caldav
    }
fi

# Run the CLI
"${PYTHON}" "${MAIN_SCRIPT}" "$@"