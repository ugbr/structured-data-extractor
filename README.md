# Structured Data Extractor

Turn messy documents into clean, typed JSON that code and databases can actually use.

Point it at an invoice, a receipt, or a contract page, and it reads the document the way a person would, then fills in a schema you defined and validates the result. Instead of "seems to work," it gives you numbers: how accurate each field is, what it costs to run per thousand documents, and how different models compare.

## Status

Early development. Being built in the open, one piece at a time. Not ready to use yet.

## The idea

Think of it as an API endpoint where the request body is a photo of paper and the response is validated JSON:

```json
{
  "vendor": "Tumen Trans LLC",
  "date": "2026-05-01",
  "total": 1250000,
  "currency": "MNT",
  "tax_id": "1234567"
}
```

A schema defines the fields you want. The model reads the document and fills them in. Validators then catch anything that does not make sense (a date that will not parse, line items that do not add up to the total, a tax ID in the wrong format) and ask the model to try again.

## What it will measure

- Per-field accuracy, not just per-document, so a single broken field cannot hide inside an otherwise good result
- Cost per 1,000 documents
- Latency
- A side-by-side comparison across a large, a mid-size, and a small model, so you can pick the cheapest one that is still accurate enough

## Stack

Python, Pydantic for the schema and validation, and the Anthropic API for the extraction.

## License

MIT
