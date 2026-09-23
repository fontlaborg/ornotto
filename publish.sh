#!/usr/bin/env bash
# this_file: publish.sh
# Release ornotto to PyPI.
#   1. ./build.sh checks and builds locally.
#   2. uvx gitnextver commits any changes, tags the next vX.Y.Z and pushes commit and tag.
#   3. The tag starts .github/workflows/wheels.yml, which builds a wheel per platform plus the sdist
#      and attaches them to a GitHub release.
#   4. This script waits for that run, downloads its artifacts and uploads them with `uv publish`.
# Needs UV_PUBLISH_TOKEN (a PyPI token) and an authenticated `gh`.
set -euo pipefail
cd "$(dirname "$0")"
[[ -n ${UV_PUBLISH_TOKEN:-} ]] || { echo "error: set UV_PUBLISH_TOKEN" >&2; exit 1; }

./build.sh
uvx gitnextver
tag=$(git describe --tags --abbrev=0)
echo "==> released $tag; waiting for the wheels workflow"

run=""
for _ in $(seq 1 60); do
  run=$(gh run list --workflow wheels.yml --branch "$tag" --json databaseId --jq '.[0].databaseId // empty')
  [[ -n $run ]] && break
  sleep 5
done
[[ -n $run ]] || { echo "error: no wheels run found for $tag" >&2; exit 1; }
gh run watch "$run" --exit-status

rm -rf dist-release
gh run download "$run" --dir dist-release --pattern 'dist-*'
mkdir -p dist-release/all
find dist-release -name '*.whl' -o -name '*.tar.gz' | xargs -I{} mv {} dist-release/all/
ls -l dist-release/all
uv publish dist-release/all/*
