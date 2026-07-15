from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from extractor.schemas import Receipt


def test_past_date_is_accepted():
    r = Receipt(company="TESCO", address="High St", date="2019-03-15", total="10")
    assert r.date == date(2019, 3, 15)


def test_future_date_is_rejected():
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError) as exc_info:
        Receipt(company="TESCO", address="High St", date=tomorrow, total="20")
    assert "later than today" in str(exc_info.value)