from datetime import date
from decimal import Decimal

from dateutil import parser as dateparser


def normalize_total(raw: str) -> Decimal:
    # strip currency symbols ($ and RM), thousands commas, and whitespace,
    # then parse what's left to a Decimal
    cleaned = raw.replace("$", "").replace("RM", "").replace(",", "").strip()
    return Decimal(cleaned)


def normalize_date(raw: str) -> date:
    # the predictions are already ISO (YYYY-MM-DD) and unambiguous, so parse
    # those exactly. dayfirst would wrongly flip an ISO string when both parts
    # are <= 12 (2018-03-10 -> 2018-10-03), so we only reach for it on the messy
    # human truth strings, where 12/01/19 means 12 jan.
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return dateparser.parse(raw, dayfirst=True).date()

def normalize_text(raw: str) -> str:
    # scoring free-text fields: casefold, then keep only letters and digits.
    # comma/period/spacing drift between label and model is cosmetic. genuine
    # differences (wrong postcode, misread letter) survive and stay misses.
    return "".join(c for c in raw.casefold() if c.isalnum())
