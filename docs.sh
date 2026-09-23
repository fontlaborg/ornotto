#!/usr/bin/env bash
# this_file: docs.sh
# Build the book: regenerate the benchmark tables from src_docs/data/, then ProperDocs + MaterialX into docs/,
# which GitHub Pages serves at https://fontlab.org/ornotto/ (branch main, folder /docs).
#   ./docs.sh           build
#   ./docs.sh serve     live preview at http://127.0.0.1:8000/ornotto/
set -euo pipefail
cd "$(dirname "$0")"
python3 src_docs/gen_tables.py
uv sync -q --group docs
cd src_docs   # pymdownx.snippets resolves its base_path (md) from the working directory
if [[ ${1:-} == serve ]]; then
  exec uv run --group docs properdocs serve
fi
uv run --group docs properdocs build --strict
cd ..
touch docs/.nojekyll   # Pages must not run Jekyll, which drops files and folders starting with "_"
echo "built $(find docs -name '*.html' | wc -l | tr -d ' ') pages into docs/"
