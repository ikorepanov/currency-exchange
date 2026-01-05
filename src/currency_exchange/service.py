from currency_exchange.models import Currency, CurrencyDto, Rate, RateDto
from currency_exchange.repositories import CurrencyRepository, RateRepository


class Service:
    currency_repository = CurrencyRepository()
    rate_repository = RateRepository()

    def get_all_currencies(self) -> list[CurrencyDto]:
        return [
            self._currency_to_dto(currency)
            for currency in self.currency_repository.get_all_currencies()
        ]

    def get_currency_with_code(self, cur_code: str) -> CurrencyDto:
        return self._currency_to_dto(
            self.currency_repository.get_currency_with_code(cur_code)
        )

    def get_currency_with_id(self, cur_id: int) -> CurrencyDto:
        return self._currency_to_dto(
            self.currency_repository.get_currency_with_id(cur_id)
        )

    def get_all_rates(self) -> list[RateDto]:
        return [
            self._rate_to_dto(rate) for rate in self.rate_repository.get_all_rates()
        ]

    def _currency_to_dto(self, currency: Currency) -> CurrencyDto:
        return CurrencyDto(
            currency.id, currency.full_name, currency.code, currency.sign
        )

    def _rate_to_dto(self, rate: Rate) -> RateDto:
        return RateDto(
            rate.id,
            self.get_currency_with_id(rate.base_id),
            self.get_currency_with_id(rate.target_id),
            rate.rate,
        )
