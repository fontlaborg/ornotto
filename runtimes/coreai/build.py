#!/usr/bin/env python3
# this_file: runtimes/coreai/build.py
"""Fetch pinned native libraries and build the optional macOS 27 bridge."""
import subprocess
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
ZOO = "2d214b3d20cdd66c9a45b57e591df407b8a0147d"
KIT = "7bdcc466204bf45fc4e994994215b2c317fb5672"

def fetch(repo, revision, prefix, destination):
    import io
    import tarfile

    with urlopen(f"https://codeload.github.com/{repo}/tar.gz/{revision}", timeout=120) as response:
        archive = response.read()
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
        for entry in bundle:
            relative = entry.name.split("/", 1)[-1]
            if not entry.isfile() or not relative.startswith(prefix):
                continue
            target = destination / relative.removeprefix(prefix)
            if not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError("unsafe upstream archive path")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bundle.extractfile(entry).read())

if __name__ == "__main__":
    fetch("john-rocky/coreai-model-zoo", ZOO, "apps/ClefFlash/", ROOT / ".upstream/ClefFlash")
    fetch("john-rocky/coreai-kit", KIT, "", ROOT / ".upstream/coreai-kit")
    # Upstream silently cuts text at either static budget. Reject it before inference.
    target = ROOT / ".upstream/coreai-kit/Sources/CoreAIKitEmbeddings/InformationExtractor.swift"
    source = target.read_text()
    replacements = {
        "let c = collate(text: text, labels: labels)": "let c = try collate(text: text, labels: labels)",
        "private func collate(text: String, labels: [String]) -> Collated": "private func collate(text: String, labels: [String]) throws -> Collated",
        "var words = wordSplit(text)": "let words = wordSplit(text)",
        "if words.count > maxWords { words = Array(words.prefix(maxWords)) }": 'if words.count > maxWords { throw VisionError.bundleLayout("STATE_TRUNCATED: text exceeds word budget") }',
        "if subwords.count + ids.count > seqLen { break }": 'if subwords.count + ids.count > seqLen { throw VisionError.bundleLayout("STATE_TRUNCATED: text exceeds token budget") }',
        "let startMap = Array(words.prefix(textWordFirst.count))": 'guard subwords.count <= seqLen else { throw VisionError.bundleLayout("STATE_TRUNCATED: schema exceeds token budget") }\n        let startMap = Array(words.prefix(textWordFirst.count))',
    }
    for before, after in replacements.items():
        assert source.count(before) == 1, f"Pinned source mismatch: {before}"
        source = source.replace(before, after)
    target.write_text(source)
    subprocess.run(["swift", "build", "-c", "release", "--package-path", str(ROOT), "--product", "ornotto-coreai"], check=True)
