class CurrencyExchangeError(Exception):
    pass


class NoDataBaseConnectionError(Exception):
    pass


class NoCurrencyError(Exception):
    pass


class NoRateError(Exception):
    pass


class CurrencyAlreadyExistsError(Exception):
    pass


class RateAlreadyExistsError(Exception):
    pass


class NoCurrencyPairError(Exception):
    pass


class CantConvertError(Exception):
    pass


class InvalidDataError(Exception):
    pass


class InvalidRequestError(Exception):
    pass
