<!-- this_file: runtimes/coreai/README.md -->

# Native Core AI bridge

Build on Apple silicon macOS 27 with Xcode's CoreAI SDK:

```sh
python3 runtimes/coreai/build.py
export ORNOTTO_COREAI_BRIDGE_BIN="$PWD/runtimes/coreai/.build/release/ornotto-coreai"
```

The build fetches immutable upstream source revisions, applies a checked patch
to reject GLiNER2 PII word/token overflow, and builds one optional executable.
`Package.resolved` pins the transitive dependencies. Downloaded source and build
outputs stay in `.upstream/` and `.build/`; neither is distributed in the sdist.
Upstream projects retain their own licences in the downloaded trees.

Python starts the executable with `clef|pii <snapshot> <fp16|int8mix>`.
It emits one JSON readiness line, then reads and answers one JSON line at a time.
Clef uses the upstream SystemOne request/response. PII accepts text, labels and
threshold; it returns native spans, UTF-16 offsets and redacted text. Errors
return a JSON error and are raised in Python. EOF exits the native process.
The Python context/managed server closes the child; pipe waits have deadlines.

Models are separate pinned downloads, never bundled. See the
[package reference](../../src_docs/md/10-package.md#native-core-ai-clef-flash-and-pii).
