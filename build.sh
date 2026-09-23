#!/usr/bin/env bash
# this_file: build.sh
# Check and build ornotto: lint, unit tests, then an sdist and a wheel for this platform in dist/.
# The wheel build compiles both engines (dohnuts.cpp and pcdServer) with CMake into build-engines/,
# which later builds reuse, and copies them to src/ornotto/_bin for editable installs.
#   ./build.sh            full build
#   ORNOTTO_ENGINES=skip ./build.sh    pure-Python wheel, no engines
set -euo pipefail
cd "$(dirname "$0")"

git submodule update --init --recursive
uvx ruff check src tests hatch_build.py examples
uv run pytest -q

rm -rf dist
uv build --sdist
uv build --wheel          # from the source tree, not the sdist: the sdist does not carry the engine sources

if [[ ${ORNOTTO_ENGINES:-} != skip ]]; then
  mkdir -p src/ornotto/_bin
  for exe in build-engines/dohnuts-cli/dohnuts-cli build-engines/pcd_server/pcd_server; do
    [[ -f $exe ]] && cp "$exe" src/ornotto/_bin/
  done
fi
ls -l dist
