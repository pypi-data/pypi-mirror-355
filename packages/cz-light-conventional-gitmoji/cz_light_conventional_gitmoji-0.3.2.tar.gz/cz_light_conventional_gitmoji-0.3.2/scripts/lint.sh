#!/usr/bin/env bash

set -e
set -x
poetry run mypy src tests || true
poetry run black src tests --check || true
poetry run pylint src tests || true