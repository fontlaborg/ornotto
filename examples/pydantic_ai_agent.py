# this_file: examples/pydantic_ai_agent.py
"""A pydantic-ai Agent whose output is decided locally: no LLM call, no API key."""

from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from ornotto.pydantic_ai import model


class Triage(BaseModel):
    """A FontLab user's request."""

    task: Literal["docs", "python", "fea"] = Field(description="What does the user want?")
    wants_code: bool = Field(description="Does the user want code they can run?")


agent = Agent(model("decider-0.8b"), output_type=Triage, instructions="Classify a FontLab user's request.")

for text in (
    "How do I open the Glyph window?",
    "Write a Python script that prints every master name",
    "Build a kern feature for A V W T",
):
    print(f"{text!r:50} -> {agent.run_sync(text).output}")
