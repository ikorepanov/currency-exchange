from dataclasses import dataclass


@dataclass
class CurrencyOld:
    id: int
    name: str
    code: str
    sign: str


@dataclass
class CurrencyDto:
    id: int
    name: str
    code: str
    sign: str


@dataclass
class Rate:
    id: int
    base_currency: CurrencyOld
    target_currency: CurrencyOld
    rate: float


@dataclass
class RateWithIds:
    id: int
    base_currency_id: int
    target_currency_id: int
    rate: float


class Currency:
    def __init__(self, id: int, code: str, full_name: str, sign: str):
        self.id = id
        self.code = code
        self.full_name = full_name
        self.sign = sign

    @property
    def code(self) -> str:
        return self._code

    @code.setter
    def code(self, value: str) -> None:
        if not (
            len(value) == 3 and value.isascii() and value.isalpha() and value.isupper()
        ):
            raise ValueError('code must be 3 uppercase English letters')
        self._code = value

    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        if not (
            value
            and all(value_part.isalpha() for value_part in value.split(' '))
            and value[0].isupper()
            and value.isascii()
        ):
            raise ValueError(
                'full_name must be in English and begin with a capital letter.'
            )
        self._full_name = value


class RateFull:
    def __init__(self, id: int, base_id: int, target_id: int, rate: float):
        self.id = id
        self.base_id = base_id
        self.target_id = target_id
        self.rate = rate

    @property
    def rate(self) -> float:
        return self._rate

    @rate.setter
    def rate(self, value: float) -> None:
        if value <= 0:
            raise ValueError('rate must be positive number')
        self._rate = float(value)
