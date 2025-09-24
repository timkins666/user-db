#!/usr/bin/env bash

# setup local environment for running directly on your machine:
# - pre-commit venv (replace)
# - backend venv (replace)
# - install frontend npm packages

PROJECT_DIR=$(git rev-parse --show-toplevel)


# PRE-COMMIT
echo Replacing pre-commit venv
rm -rf "$PROJECT_DIR/.venv" 2> /dev/null

python3 -m venv "$PROJECT_DIR/.venv"

# shellcheck source=/dev/null
source "$PROJECT_DIR/.venv/bin/activate"

pip install pre-commit


# BACKEND - uses uv from root venv
echo Replacing fastapi backend venv

cd "$PROJECT_DIR/backend-fastapi" || exit 1

rm -rf .venv 2> /dev/null

python -m venv .venv
# shellcheck source=/dev/null
source .venv/bin/activate

pip install uv
uv sync --all-groups


# FRONTEND
echo Installing frontend npm packages

cd "$PROJECT_DIR/frontend" || exit 1

npm install
