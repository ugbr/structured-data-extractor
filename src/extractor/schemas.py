from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class Receipt(BaseModel):
    company: str
    address: str
    date: date
    total: Decimal = Field(gt=0)

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError(f'{value} is later than today!')
        return value