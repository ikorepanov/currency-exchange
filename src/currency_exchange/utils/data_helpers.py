import json
from dataclasses import asdict
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from currency_exchange.constants import NUMBER_OF_DECIMAL_PLACES_FOR_JSON
from currency_exchange.dtos import (
    CurrencyDto,
    ExchangeDto,
    RateDto,
)


def serialize(
    data: CurrencyDto | RateDto | ExchangeDto | list[CurrencyDto] | list[RateDto],
) -> str:
    if isinstance(data, (CurrencyDto, RateDto, ExchangeDto)):
        return to_json(to_dict(data))
    else:
        return to_json([to_dict(obj) for obj in data])


def to_json(obj: dict[str, Any] | list[dict[str, Any]]) -> str:
    return json.dumps(obj, ensure_ascii=False)


def to_dict(dto_obj: CurrencyDto | RateDto | ExchangeDto) -> dict[str, Any]:
    dict_obj = asdict(dto_obj)
    for key, value in dict_obj.items():
        if isinstance(value, Decimal):
            rounded_value = round_decimal(value, NUMBER_OF_DECIMAL_PLACES_FOR_JSON)
            dict_obj[key] = float(rounded_value)
    converted_keys_dict_obj = convert_keys(dict_obj)
    return converted_keys_dict_obj


def round_decimal(value_dec: Decimal, places: int) -> Decimal:
    return value_dec.quantize(Decimal('1').scaleb(-places), rounding=ROUND_HALF_UP)


def convert_keys(original: dict[str, Any]) -> dict[str, Any]:
    return {
        (to_lower_camel_case(key) if '_' in key else key): value
        for key, value in original.items()
    }


def to_lower_camel_case(snake_str: str) -> str:
    camel_string = to_camel_case(snake_str)
    return snake_str[0].lower() + camel_string[1:]


def to_camel_case(snake_str: str) -> str:
    return ''.join(letter.capitalize() for letter in snake_str.lower().split('_'))


def repl_dec_separator(value: str) -> str:
    return value.replace(',', '.')
