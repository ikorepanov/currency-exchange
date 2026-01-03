from dataclasses import dataclass

from forex_python.converter import CurrencyCodes


@dataclass
class Currency:
    id: int
    name: str
    code: str
    sign: str


@dataclass
class Rate:
    id: int
    base_currency: Currency
    target_currency: Currency
    rate: float


class CurrencyFull:
    signs = CurrencyCodes()

    def __init__(self, id: int, code: str, full_name: str):
        self.id = id
        self.code = code
        self.full_name = full_name

        self.sign = self.signs.get_symbol(code)

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
        if not (value and self.is_title(value) and value.isascii() and value.isalpha()):
            raise ValueError(
                'Each word in full_name must start with a capital English letter. '
                'The rest of the letters in words must be in lowercase English letters.'
            )
        self._full_name = value

    def is_title(self, s: str) -> bool:
        return all(word[0].isupper() and word[1:].islower() for word in s.split())


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
