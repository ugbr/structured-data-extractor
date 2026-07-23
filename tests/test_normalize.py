from datetime import date
from decimal import Decimal

from extractor.normalize import normalize_date, normalize_text, normalize_total

# --- total ---

def test_total_strips_dollar_and_trailing_zero():
    assert normalize_total("$8.20") == Decimal("8.20")


def test_total_compares_by_value_not_string():
    # "8.2" and "$8.20" are the same money, so they must normalize equal
    assert normalize_total("8.2") == normalize_total("$8.20")


def test_total_strips_ringgit_and_whitespace():
    assert normalize_total("RM 60.30") == Decimal("60.30")


# --- date ---

def test_date_parses_dayfirst_truth():
    # malaysian receipts are day-first: 12/01/19 is 12 jan, not 1 dec
    assert normalize_date("12/01/19") == date(2019, 1, 12)


def test_date_parses_spelled_month():
    assert normalize_date("10 MAR 2018") == date(2018, 3, 10)


def test_date_swaps_when_dayfirst_impossible():
    # 28 can't be a month, so this us-order date still lands on dec 28
    assert normalize_date("12/28/2017") == date(2017, 12, 28)


def test_iso_prediction_is_not_flipped():
    # regression: dayfirst used to corrupt the already-iso predictions,
    # turning 2018-03-10 (10 mar) into 2018-10-03 (3 oct). it must not.
    assert normalize_date("2018-03-10") == date(2018, 3, 10)


def test_iso_prediction_matches_spelled_truth():
    assert normalize_date("2018-03-10") == normalize_date("10 MAR 2018")


# --- text (company / address) ---

def test_text_ignores_punctuation_and_spacing():
    assert normalize_text("27, JALAN") == normalize_text("27,JALAN")


def test_text_is_case_insensitive():
    assert normalize_text("Tesco") == normalize_text("TESCO")


def test_text_keeps_genuine_differences():
    # a real misread must stay a miss: KL is not XL
    assert normalize_text("52000 KL") != normalize_text("52000 XL")
