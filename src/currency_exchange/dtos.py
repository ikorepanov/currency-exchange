from dataclasses import dataclass
from decimal import Decimal


@dataclass
class CurrencyDto:
    id: int
    name: str
    code: str
    sign: str


@dataclass
class CurrencyPostDto:
    name: str
    code: str
    sign: str


@dataclass
class RateDto:
    id: int
    base_currency: CurrencyDto
    target_currency: CurrencyDto
    rate: Decimal


@dataclass
class RatePostUpdateDto:
    base_currency_code: str
    target_currency_code: str
    rate: Decimal


@dataclass
class ExchangeDto:
    base_currency: CurrencyDto
    target_currency: CurrencyDto
    rate: Decimal
    amount: Decimal
    converted_amount: Decimal


@dataclass
class ExchangePostDto:
    from_currency_code: str
    to_currency_code: str
    amount: Decimal
