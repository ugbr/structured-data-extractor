# Structured Data Extractor

Turns a scanned receipt into typed, validated JSON, and measures how well it does it. You define the fields you want as a schema, point it at a receipt, and get back a checked object plus real numbers: per-field accuracy against hand-verified labels, cost per 1,000 documents, and latency, compared across models so you can pick the cheapest one that is still accurate enough.

The target document is a scanned store receipt. The fields are the flat set most receipts share: company, address, date, and total.

## What you get back

The schema is the contract. The model reads the receipt text and fills it in, and validators reject anything that does not make sense (a date that will not parse, a date in the future, a total that is not a positive number).

```json
{
  "company": "SHELL ISNI PETRO TRADING",
  "address": "LOT 2685 JLN GENTING KLANG 53300 KL SITE 1066",
  "date": "2018-03-18",
  "total": "86.00"
}
```

## Results

Scored against 50 hand-verified receipts from SROIE, per field. Cost is per 1,000 documents at list price and at Batch API price (half of list), latency is the median per-call time.

| model | company | address | date | total | cost/1k | cost/1k (batch) | p50 |
|-------|---------|---------|------|-------|---------|-----------------|-----|
| Opus 4.8 | 46/50 | 39/50 | 50/50 | 50/50 | $7.03 | $3.52 | 2.70s |
| Sonnet 5 | 44/50 | 39/50 | 50/50 | 50/50 | $4.24 | $2.12 | 3.81s |
| Haiku 4.5 | 43/50 | 39/50 | 50/50 | 50/50 | $1.10 | $0.55 | 1.46s |

The accuracy is basically flat. Date and total are perfect everywhere, address is a dead tie, and company is within three points. When quality ties like that, cost and latency make the call, and the small model wins both: Haiku is the cheapest and the fastest, and three points of company is the only thing you give up for it. Running through the Batch API halves the bill without changing the ranking, so the production number is Haiku in batch, about 55 cents per 1,000 receipts.

Paying up for a frontier model buys almost nothing here. Opus over Haiku is 6.4x the cost for three points of company and nothing else.

## The hard field

Address is the field that does not reach 50, and it is worth being honest about why, because the reasons are not all the model's fault. The misses split three ways:

- **The model dropped part of the address.** Some receipts print a branch or site line below the street address, like `SITE 1066`, and the model cuts it off. This one is real and fixable: a sharper field description gets the model to keep it.
- **The labels disagree with each other.** Some receipts print an outlet name in parentheses after the address. On one receipt the ground-truth label keeps it, and on another receipt from the same chain with the same street address the label drops it. No instruction can match both, because the target contradicts itself.
- **The character was already wrong before the model saw it.** The pipeline runs on the dataset's OCR text, not the image, and the OCR sometimes misreads a character (a postcode comes through as `81760` instead of `81750`, a `KL` as `XL`). The correct value is not in the input, so there is nothing for the model to copy or fix. Only feeding the image instead of the text could help, which is a different pipeline.

One more thing worth naming: trying to fix the first case with a stronger prompt made the model over-include on the company field too (it started keeping the store's registration number and the owner's name), and once you account for run-to-run variance the net gain washed out. So the shipped schema keeps the field descriptions plain. The truncation is promptable in isolation, but not for free.

## About the numbers

SROIE is a well-known public dataset from 2019, which means these models have very likely seen it during training. Treat the accuracy here as an upper bound, not a field measurement, the same way you would not trust a student's score on an exam they already had the answer key to. An honest benchmark needs a fresh set the models have not seen: a small batch of invoices printed and photographed by hand, scored the same way and reported next to these numbers. That is a planned follow-up and is not in here yet.

## How it works

1. Load a receipt's OCR text (SROIE ships the OCR output alongside each image).
2. Send it to the Anthropic API with the schema attached, so the response comes back as structured JSON that already matches the shape.
3. Parse it into a Pydantic model, which enforces the types and the validators.
4. Normalize each field and score it against the hand-verified label (dates parsed rather than string-matched, money compared as decimals, free text compared on letters and digits so punctuation drift does not count as a miss).

## Running it

You need [uv](https://docs.astral.sh/uv/), an Anthropic API key, and the SROIE data.

```bash
# install deps
uv sync

# set your key
cp .env.example .env   # then edit .env and paste your key

# get SROIE and put it under data/documents/sroie/ with img/, box/, and
# key/ subfolders (id.jpg, id.csv, id.json per receipt).
# corrected mirror: https://github.com/zzzDavid/ICDAR-2019-SROIE

# run one model over the sample and cache the predictions
uv run --env-file .env python -m extractor.predict haiku   # or opus, sonnet

# score everything and print the table
uv run python -m extractor.evaluate
```

The 50 hand-verified labels are included, in `data/ground_truth/verified.jsonl`. The SROIE documents themselves are not committed; grab them from the mirror above.

## Stack

Python, Pydantic for the schema and validation, the Anthropic API for the extraction, uv for packaging.

## License

MIT
