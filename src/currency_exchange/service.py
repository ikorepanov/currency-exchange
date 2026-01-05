from currency_exchange.models import Currency, CurrencyDto
from currency_exchange.repository import Repository


class Service:
    repository = Repository()

    def get_all_currencies(self) -> list[CurrencyDto]:
        return [
            self.to_dto(currency) for currency in self.repository.get_all_currencies()
        ]

    def get_one_currency(self, cur_code: str) -> CurrencyDto:
        return self.to_dto(self.repository.get_one_currency(cur_code))

    def to_dto(self, currency: Currency) -> CurrencyDto:
        return CurrencyDto(
            currency.id, currency.full_name, currency.code, currency.sign
        )
