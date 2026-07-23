"""Score cached predictions and build the model comparison table.

The reusable pieces (load a JSONL by id, score one field, cost per 1k, p50
latency) live here as plain functions, so anything can import them. Run this
module directly to print the comparison table across all models.

Run it with:
    uv run python -m extractor.evaluate
"""

import json
from pathlib import Path
from statistics import median

from .normalize import normalize_date, normalize_text, normalize_total

TRUTH_PATH = Path("data/ground_truth/verified.jsonl")
FIELDS = ["company", "address", "date", "total"]
MODELS = ["opus", "sonnet", "haiku"]

# field -> how to canonicalize it before comparing. missing = compare raw.
NORMALIZERS = {
    "date": normalize_date,
    "total": normalize_total,
    "company": normalize_text,
    "address": normalize_text,
}

# per-model price in dollars per 1,000,000 tokens. sonnet is list price, not the
# intro discount, so the numbers stay true past the intro window.
PRICES = {
    "opus": {"input": 5.00, "output": 25.00},
    "sonnet": {"input": 3.00, "output": 15.00},
    "haiku": {"input": 1.00, "output": 5.00},
}


def load_by_id(path):
    """Read a JSONL file and return {id: row}, so we can look a receipt up by id."""
    rows = {}
    for line in path.read_text().splitlines():
        record = json.loads(line)
        rows[record["id"]] = record
    return rows


def field_matches(field, pred_value, truth_value):
    """True if the prediction matches ground truth for this field, after normalizing."""
    norm = NORMALIZERS.get(field)
    if norm is None:
        return pred_value == truth_value
    try:
        return norm(pred_value) == norm(truth_value)
    except Exception:
        # a value that won't normalize can't be a match
        return False


def cost_per_1000(rows, slug, batch=False):
    """Dollars to run 1,000 documents through this model, from its saved token counts."""
    price = PRICES[slug]
    total = 0.0
    for row in rows:
        total += (row["input_tokens"] / 1_000_000 * price["input"]
                  + row["output_tokens"] / 1_000_000 * price["output"])
    return total * 20 * (0.5 if batch else 1)  # 50 receipts -> 1,000 docs


def latency_p50(rows):
    """Median per-call latency, in seconds. Robust to the odd slow call."""
    return median(row["latency_s"] for row in rows)


def print_table():
    truth = load_by_id(TRUTH_PATH)
    ids = sorted(truth)  # the 50 verified ids are what we score against

    header = (
        f"{'model':8} {'company':>8} {'address':>8} "
        f"{'date':>6} {'total':>6} {'cost/1k':>9} {'cost/1k(b)':>9} {'p50':>7}"
    )
    print(header)
    print("-" * len(header))

    for slug in MODELS:
        preds = load_by_id(Path(f"results/predictions_{slug}.jsonl"))
        rows = list(preds.values())

        cells = []
        for field in FIELDS:
            hits = sum(
                1 for rid in ids
                if field_matches(field, preds[rid][field], truth[rid][field])
            )
            cells.append(f"{hits}/{len(ids)}")

        cost = f"${cost_per_1000(rows, slug):.2f}"
        cost_batch = f"${cost_per_1000(rows, slug, batch=True):.2f}"
        p50 = f"{latency_p50(rows):.2f}s"
        print(
            f"{slug:8} {cells[0]:>8} {cells[1]:>8} {cells[2]:>6} "
            f"{cells[3]:>6} {cost:>9} {cost_batch:>9} {p50:>7}"
        )


if __name__ == "__main__":
    print_table()
