"""Generate and cache predictions for one model across the SROIE slice.

Runs the extractor over the first 50 receipts concurrently and writes each
prediction, with its token counts and latency, to
results/predictions_<slug>.jsonl. The run is split from scoring on purpose: this
part costs money and we do it once per model, scoring is free and repeatable.

Run it with:
    uv run --env-file .env python -m extractor.predict haiku
"""

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from anthropic import Anthropic

from .extract import extract_receipt
from .sroie import load_text

MODELS = {
    "opus": "claude-opus-4-8",
    "sonnet": "claude-sonnet-5",
    "haiku": "claude-haiku-4-5-20251001",
}


def extract_one(rid, client, model_id):
    """Extract one receipt and flatten the result into a JSON-safe row."""
    result = extract_receipt(load_text(rid), client, model_id)
    row = {"id": rid, **result.receipt.model_dump(mode="json")}
    row["input_tokens"] = result.input_tokens
    row["output_tokens"] = result.output_tokens
    row["latency_s"] = result.latency_s
    row["model"] = result.model
    return row


def run(slug):
    model_id = MODELS[slug]
    out_path = Path(f"results/predictions_{slug}.jsonl")
    client = Anthropic()  # one client, reused across all 50 calls
    ids = [f"{i:03d}" for i in range(50)]
    records = []
    failures = []

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=8) as pool:
        future_to_id = {pool.submit(extract_one, rid, client, model_id): rid for rid in ids}
        for future in as_completed(future_to_id):
            rid = future_to_id[future]
            try:
                row = future.result()
                records.append(row)
                print(rid, "ok  ", row["total"])
            except Exception as e:
                failures.append((rid, e))
                print(rid, "FAIL", type(e).__name__)
    elapsed = time.perf_counter() - start

    # as_completed hands them back in finish order, so sort by id for a tidy file
    records.sort(key=lambda r: r["id"])
    with out_path.open("w") as f:
        for row in records:
            f.write(json.dumps(row) + "\n")

    print(f"\n{len(records)} ok, {len(failures)} failed in {elapsed:.1f}s")
    print(f"wrote {len(records)} predictions to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in MODELS:
        sys.exit(f"usage: python -m extractor.predict <{'|'.join(MODELS)}>")
    run(sys.argv[1])
