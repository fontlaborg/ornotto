# this_file: src/ornotto/__main__.py
"""The `ornotto` command line.

ornotto models                                  list registered models
ornotto pull decider-0.8b                       download a model
ornotto choose "Build a kern feature" docs python fea
ornotto check "Rename all .sc glyphs" "Does the user want code?"
ornotto serve decider-0.8b --engine=pcd         run an engine in the foreground, print its URL
"""

from __future__ import annotations

import json
import time

import fire

from . import MODELS, Decider, __version__
from ._engines import Server
from ._models import resolve


class Cli:
    """Typed decisions on local models (dohnuts and pcdServer)."""

    def version(self) -> str:
        return __version__

    def models(self) -> str:
        """List registered models."""
        rows = [f"{'name':16} {'engines':13} {'family':11} {'GB':>4}  licence"]
        for m in MODELS.values():
            rows.append(f"{m.name:16} {','.join(m.engines):13} {m.family:11} {m.size_gb:4.1f}  {m.license}")
        return "\n".join(rows)

    def pull(self, model: str) -> str:
        """Download a model (and its metadata) into the Hugging Face cache."""
        return str(resolve(model).gguf)

    def choose(
        self,
        state: str,
        *options: str,
        model: str = "decider-0.8b",
        engine: str | None = None,
        question: str | None = None,
    ) -> str:
        """Pick one option; prints the answer as JSON."""
        answer = Decider(model, engine=engine).choose(state, list(options), question)
        return json.dumps({"choice": answer.value, "probabilities": answer.probabilities})

    def check(self, state: str, question: str, model: str = "decider-0.8b", engine: str | None = None) -> str:
        """Answer yes or no; prints the probability of yes as JSON."""
        answer = Decider(model, engine=engine).check(state, question)
        return json.dumps({"yes": answer.value, "probability": answer.probability})

    def serve(self, model: str = "decider-0.8b", engine: str | None = None) -> None:
        """Start an engine and keep it running until Ctrl-C."""
        decider = Decider(model, engine=engine)
        print(f"{decider.engine} serving {decider.model_name} at {decider.url}", flush=True)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            Server.stop_all()


def main() -> None:
    fire.Fire(Cli, name="ornotto")


if __name__ == "__main__":
    main()
