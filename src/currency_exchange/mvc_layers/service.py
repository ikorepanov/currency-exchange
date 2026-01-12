from functools import cached_property

from currency_exchange.dtos import (
    CurrencyDto,
    CurrencyPostDto,
    ExchangeDto,
    ExchangePostDto,
    RateDto,
    RatePostUpdateDto,
)
from currency_exchange.exceptions import (
    CantConvertError,
    InvalidDataError,
    InvalidRequestError,
    NoRateError,
)
from currency_exchange.models import Currency, Rate
from currency_exchange.mvc_layers.repositories import CurrencyRepository, RateRepository
from currency_exchange.utils.validation import is_valid, is_valid_cur_code


class Service:
    def get_currencies(self) -> list[CurrencyDto]:
        currencies = self.currency_repository.get_currencies()
        return [self._currency_to_dto(currency) for currency in currencies]

    def get_currency(self, cur_code: str) -> CurrencyDto:
        if is_valid(cur_code):
            currency = self.currency_repository.get_currency(cur_code)
            return self._currency_to_dto(currency)
        raise InvalidRequestError(
            'Код валюты должен состоять из 3 заглавных английских букв'
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

    def get_rate(self, code_pair: str) -> RateDto:
        base_currency_dto = self.get_currency(code_pair[:3])
        target_currency_dto = self.get_currency(code_pair[3:])
        return self._rate_to_dto(
            self.rate_repository.get_rate_with_cur_ids(
                base_currency_dto.id, target_currency_dto.id
            ),
            base_currency_dto,
            target_currency_dto,
        )

    def save_currency(self, currency_dto: CurrencyPostDto) -> CurrencyDto:
        currency = Currency(
            None, currency_dto.code, currency_dto.name, currency_dto.sign
        )
        currency_with_id = self.currency_repository.save_currency(currency)
        return self._currency_to_dto(currency_with_id)

    def save_rate(self, rate_post_dto: RatePostUpdateDto) -> RateDto:
        base_currency_code = rate_post_dto.base_currency_code
        target_currency_code = rate_post_dto.target_currency_code

        if is_valid_cur_code(base_currency_code) and is_valid_cur_code(
            target_currency_code
        ):
            base_currency_dto = self.get_currency(rate_post_dto.base_currency_code)
            target_currency_dto = self.get_currency(rate_post_dto.target_currency_code)
        else:
            raise InvalidDataError

        rate = Rate(
            None, base_currency_dto.id, target_currency_dto.id, rate_post_dto.rate
        )
        return self._rate_to_dto(
            self.rate_repository.save_rate(rate), base_currency_dto, target_currency_dto
        )

    def update_rate(self, rate_update_dto: RatePostUpdateDto) -> RateDto:
        base_currency_dto = self.get_currency(rate_update_dto.base_currency_code)
        target_currency_dto = self.get_currency(rate_update_dto.target_currency_code)
        rate = Rate(
            None,
            base_currency_dto.id,
            target_currency_dto.id,
            rate_update_dto.rate,
        )
        return self._rate_to_dto(
            self.rate_repository.update_rate(rate),
            base_currency_dto,
            target_currency_dto,
        )

    def exchange_currencies(self, exchange_post_dto: ExchangePostDto) -> ExchangeDto:
        from_currency_code = exchange_post_dto.from_currency_code
        to_currency_code = exchange_post_dto.to_currency_code
        amount = exchange_post_dto.amount

        try:
            exch_rate = self.get_rate(from_currency_code + to_currency_code)
            rate = exch_rate.rate
        except NoRateError:
            try:
                reversed_rate = self.get_rate(to_currency_code + from_currency_code)
                rate = reversed_rate.rate
            except NoRateError:
                try:
                    base_cur_dto = self.get_currency(from_currency_code)
                    target_cur_dto = self.get_currency(to_currency_code)

                    interm_rate_1 = self.get_rate('USD' + from_currency_code)
                    interm_rate_2 = self.get_rate('USD' + to_currency_code)
                    rate = interm_rate_2.rate / interm_rate_1.rate
                except NoRateError:
                    raise CantConvertError()
                return ExchangeDto(
                    base_cur_dto,
                    target_cur_dto,
                    rate,
                    amount,
                    rate * amount,
                )
            return ExchangeDto(
                reversed_rate.target_currency,
                reversed_rate.base_currency,
                rate,
                amount,
                rate * amount,
            )
        return ExchangeDto(
            exch_rate.base_currency,
            exch_rate.target_currency,
            rate,
            amount,
            rate * amount,
        )

    @cached_property
    def currency_repository(self) -> CurrencyRepository:
        return CurrencyRepository()

    @cached_property
    def rate_repository(self) -> RateRepository:
        return RateRepository()

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
        if rate.id is not None:
            id = rate.id
        return RateDto(
            id,
            base_currency_dto,
            target_currency_dto,
            rate.rate,
        )
