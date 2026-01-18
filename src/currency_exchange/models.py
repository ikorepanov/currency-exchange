from dataclasses import dataclass
from decimal import Decimal


class Currency:
    def __init__(self, id: int | None, code: str, full_name: str, sign: str):
        self.id = id
        self.code = code
        self.full_name = full_name
        self.sign = sign

    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, value: int | None) -> None:
        self._id = value

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
            raise ValueError('name must be in English letters and begin with a capital')
        self._full_name = value


@dataclass
class Rate:
    id: int | None
    base_id: int
    target_id: int
    rate: Decimal
