from unicodedata import category


def is_valid_name(name: str) -> bool:
    return ''.join(name.split(' ')).isalpha() and name.isascii() and name[0].isupper()


def is_valid_sign(sign: str) -> bool:
    return len(sign) == 1 and category(sign) == 'Sc'


def is_valid_cur_code(cur_code: str) -> bool:
    return (
        cur_code.isalpha()
        and cur_code.isascii()
        and cur_code.isupper()
        and len(cur_code) == 3
    )


def is_positive_number(value: str) -> bool:
    try:
        return float(value) > 0
    except ValueError:
        return False
