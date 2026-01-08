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


class Rate:
    def __init__(self, id: int | None, base_id: int, target_id: int, rate: float):
        self.id = id
        self.base_id = base_id
        self.target_id = target_id
        self.rate = rate

    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, value: int | None) -> None:
        self._id = value

    @property
    def rate(self) -> float:
        return self._rate

    @rate.setter
    def rate(self, value: float) -> None:
        if not (value > 0 and self.is_proper_decimal(value)):
            raise ValueError(
                'rate must be positive number with not more than 6 decimal places'
            )
        self._rate = float(value)

    def is_proper_decimal(self, value: float) -> bool:
        d = Decimal(str(value))
        return abs(int(d.as_tuple().exponent)) <= 6
