def is_valid_pair(code_pair: str) -> bool:
    return (
        code_pair.isalpha()
        and code_pair.isascii()
        and code_pair.isupper()
        and len(code_pair) == 6
    )


def is_valid_cur_code(cur_code: str) -> bool:
    return (
        cur_code.isalpha()
        and cur_code.isascii()
        and cur_code.isupper()
        and len(cur_code) == 3
    )


def is_valid(cur_code: str) -> bool:
    return cur_code.isascii() and cur_code.isupper() and len(cur_code) == 3


def is_valid_amount(str_amount: str) -> bool:
    if _is_amount_could_be_float(str_amount):
        return float(str_amount) > 0
    else:
        return False


def _is_amount_could_be_float(str_amount: str) -> bool:
    try:
        float(str_amount)
        return True
    except ValueError:
        return False
