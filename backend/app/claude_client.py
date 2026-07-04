"""Claude API client for the client-facing advisory memo.

Claude only ever turns the already-computed structured JSON into prose —
it never calculates or decides financial logic, and is instructed not to
change any numbers.
"""

import json
import os

import anthropic

SYSTEM_PROMPT = (
    "Write a professional wealth advisory summary for an NRI client based on "
    "this JSON. Do not change any numbers."
)

MODEL = "claude-sonnet-5"
MAX_TOKENS = 4096


def generate_wealth_memo(structured_plan: dict) -> str:
    """Call the Claude API to turn the structured wealth plan into prose."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(structured_plan)}],
    )
    return response.content[0].text
