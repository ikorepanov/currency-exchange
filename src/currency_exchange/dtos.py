from dataclasses import dataclass


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
    rate: float


@dataclass
class RatePostDto:
    base_currency_code: str
    target_currency_code: str
    rate: float
