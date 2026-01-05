from currency_exchange.models import Currency, CurrencyDto
from currency_exchange.repository import Repository


class Service:
    repository = Repository()

    def get_all_currencies(self) -> list[Currency]:
        return self.repository.get_all_currencies()

    def to_dto(self, currency: Currency) -> CurrencyDto:
        return CurrencyDto(
            currency.id, currency.full_name, currency.code, currency.sign
        )
