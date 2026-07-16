import time
from dataclasses import dataclass

from anthropic import Anthropic

from .schemas import Receipt


@dataclass
class ExtractionResult:
    """One extraction call: what came back, and what it cost."""

    receipt: Receipt
    model: str
    input_tokens: int
    output_tokens: int
    latency_s: float


def extract_receipt(text: str, model: str = "claude-opus-4-8") -> ExtractionResult:
    client = Anthropic()
    start = time.perf_counter()

    response = client.messages.parse(
        model=model,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"Extract the fields from this receipt:\n\n{text}",
        }],
        output_format=Receipt,
    )

    elapsed = time.perf_counter() - start
    result = ExtractionResult(
        receipt=response.parsed_output, 
        model=model, 
        input_tokens=response.usage.input_tokens, 
        output_tokens=response.usage.output_tokens,
        latency_s=elapsed
    )
    return result