#!/usr/bin/env bash
# this_file: test.sh
# Run every check: lint, unit tests, then (with ENGINES=1) the real-engine tests and the examples.
# The engine run loads decider-0.8b on each engine in turn, one process at a time.
set -euo pipefail
cd "$(dirname "$0")"

uvx ruff check src tests hatch_build.py examples
uvx ruff format --check src tests hatch_build.py examples
uv run pytest -q

if [[ ${ENGINES:-0} == 1 ]]; then
  uv run pytest -q -m engine
  for example in examples/*.py; do
    echo "== $example"
    uv run python "$example"
  done
fi
