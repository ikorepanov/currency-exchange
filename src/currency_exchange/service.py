from currency_exchange.models import Currency, CurrencyDto


class Service:
    def to_dto(self, currency: Currency) -> CurrencyDto:
        return CurrencyDto(
            currency.id, currency.full_name, currency.code, currency.sign
        )
