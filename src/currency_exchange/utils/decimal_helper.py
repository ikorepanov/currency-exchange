from decimal import ROUND_HALF_UP, Decimal


def to_decimal(rate_str: str) -> Decimal:
    return Decimal(rate_str).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
