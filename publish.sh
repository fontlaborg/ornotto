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

# gitnextver tags only when it has something to commit, so the release itself is that change: the
# CHANGELOG's "Unreleased" section is dated under the version gitnextver is about to tag (patch + 1).
last=$(git tag -l 'v[0-9]*.[0-9]*.[0-9]*' | sort -V | tail -1)
IFS=. read -r major minor patch <<< "${last#v}"
next="v$major.$minor.$((patch + 1))"
grep -q '^## Unreleased' CHANGELOG.md || { echo "error: CHANGELOG.md has no '## Unreleased' section" >&2; exit 1; }
sed -i.bak "s/^## Unreleased\$/## Unreleased\n\n## ${next#v} ($(date +%Y-%m-%d))/" CHANGELOG.md && rm CHANGELOG.md.bak

uvx gitnextver
tag=$(git describe --tags --abbrev=0)
[[ $tag == "$next" ]] || { echo "error: expected tag $next, gitnextver left $tag" >&2; exit 1; }
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
