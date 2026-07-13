from datetime import date
from decimal import Decimal

from pydantic import BaseModel

class Receipt(BaseModel):
    company: str
    address: str
    date: date
    total: Decimal