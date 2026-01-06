from currency_exchange.models import (
    Currency,
    CurrencyDto,
    CurrencyPostDto,
    Rate,
    RateDto,
)
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
            self._rate_to_dto(
                rate,
                self.get_currency_with_id(rate.base_id),
                self.get_currency_with_id(rate.target_id),
            )
            for rate in self.rate_repository.get_all_rates()
        ]

    def get_rate_with_cur_ids(self, code_pair: str) -> RateDto:
        base_currency_dto = self.get_currency_with_code(code_pair[:3])
        target_currency_dto = self.get_currency_with_code(code_pair[3:])
        rate = self.rate_repository.get_rate_with_cur_ids(
            base_currency_dto.id, target_currency_dto.id
        )
        return RateDto(
            rate.id,
            base_currency_dto,
            target_currency_dto,
            rate.rate,
        )

    def save_currency(self, currency_dto: CurrencyPostDto) -> CurrencyDto:
        currency = Currency(
            None, currency_dto.code, currency_dto.name, currency_dto.sign
        )
        currency_with_id = self.currency_repository.save_currency(currency)
        return self._currency_to_dto(currency_with_id)

    def _currency_to_dto(self, currency: Currency) -> CurrencyDto:
        if currency.id is not None:
            id = currency.id
        return CurrencyDto(id, currency.full_name, currency.code, currency.sign)

    def _rate_to_dto(
        self,
        rate: Rate,
        base_currency_dto: CurrencyDto,
        target_currency_dto: CurrencyDto,
    ) -> RateDto:
        return RateDto(
            rate.id,
            base_currency_dto,
            target_currency_dto,
            rate.rate,
        )
