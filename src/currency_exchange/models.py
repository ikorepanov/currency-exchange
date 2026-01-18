from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Currency:
    id: int | None
    code: str
    full_name: str
    sign: str


@dataclass
class Rate:
    id: int | None
    base_id: int
    target_id: int
    rate: Decimal
