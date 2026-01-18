from functools import cached_property
from typing import NamedTuple

from currency_exchange.constants import EXCHANGE_RATE_HELPER_CUR_CODE
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
    NoCurrencyError,
    NoCurrencyPairError,
    NoRateError,
)
from currency_exchange.models import Currency, Rate
from currency_exchange.mvc_layers.repository import Repository


class CurrenciesInfo(NamedTuple):
    currency_1: Currency
    currency_2: Currency
    currency_1_id: int
    currency_2_id: int


class Service:
    def get_currencies(self) -> list[CurrencyDto]:
        currencies = self.repository.get_currencies()
        return [self._currency_to_dto(currency) for currency in currencies]

    def get_currency(self, cur_code: str) -> CurrencyDto:
        currency = self.repository.get_currency(cur_code)
        return self._currency_to_dto(currency)

    def get_rates(self) -> list[RateDto]:
        rates = self.repository.get_rates()
        return [
            self._rate_to_dto(
                rate,
                self.repository.get_currency_by_id(rate.base_id),
                self.repository.get_currency_by_id(rate.target_id),
            )
            for rate in rates
        ]

    def get_rate(self, code_pair: str) -> RateDto:
        try:
            base_currency, target_currency, base_currency_id, target_currency_id = (
                self._resolve_code_pair(code_pair[:3], code_pair[3:])
            )
        except NoCurrencyError:
            raise NoRateError(
                'Обменный курс для пары не найден, так как не найдена одна '
                'или обе валюты'
            )

        rate = self.repository.get_rate(base_currency_id, target_currency_id)
        return self._rate_to_dto(rate, base_currency, target_currency)

    def create_currency(self, currency_post_dto: CurrencyPostDto) -> CurrencyDto:
        cur_code = currency_post_dto.code
        cur_name = currency_post_dto.name
        cur_sign = currency_post_dto.sign
        currency = Currency(None, cur_code, cur_name, cur_sign)
        currency_with_id = self.repository.create_currency(currency)
        return self._currency_to_dto(currency_with_id)

    def create_rate(self, rate_post_dto: RatePostUpdateDto) -> RateDto:
        base_cur_code = rate_post_dto.base_currency_code
        target_cur_code = rate_post_dto.target_currency_code
        rate = rate_post_dto.rate

        try:
            base_currency, target_currency, base_currency_id, target_currency_id = (
                self._resolve_code_pair(base_cur_code, target_cur_code)
            )
        except NoCurrencyError:
            raise NoCurrencyPairError(
                'Одна (или обе) валюта из валютной пары не существует в БД'
            )

        exchange_rate = Rate(None, base_currency_id, target_currency_id, rate)
        exchange_rate_with_id = self.repository.create_rate(exchange_rate)
        return self._rate_to_dto(exchange_rate_with_id, base_currency, target_currency)

    def update_rate(self, rate_update_dto: RatePostUpdateDto) -> RateDto:
        base_cur_code = rate_update_dto.base_currency_code
        target_cur_code = rate_update_dto.target_currency_code
        rate = rate_update_dto.rate

        try:
            base_currency, target_currency, base_currency_id, target_currency_id = (
                self._resolve_code_pair(base_cur_code, target_cur_code)
            )
        except NoCurrencyError:
            raise NoRateError(
                'Валютная пара отсутствует в базе данных, так как не найдена одна '
                'или обе валюты'
            )

        exchange_rate = Rate(None, base_currency_id, target_currency_id, rate)
        exchange_rate_with_id = self.repository.update_rate(exchange_rate)
        return self._rate_to_dto(exchange_rate_with_id, base_currency, target_currency)

    def exchange_currencies(self, exchange_post_dto: ExchangePostDto) -> ExchangeDto:
        from_cur_code = exchange_post_dto.from_currency_code
        to_cur_code = exchange_post_dto.to_currency_code
        amount = exchange_post_dto.amount

        try:
            from_currency, to_currency, from_currency_id, to_currency_id = (
                self._resolve_code_pair(from_cur_code, to_cur_code)
            )
        except NoCurrencyError:
            raise CantConvertError(
                'Расчёт перевода невозможен, так как не найдена одна или обе валюты'
            )

        try:
            exchange_rate = self.repository.get_rate(from_currency_id, to_currency_id)
            rate = exchange_rate.rate
        except NoRateError:
            try:
                reversed_exchange_rate = self.repository.get_rate(
                    to_currency_id, from_currency_id
                )
                rate = 1 / reversed_exchange_rate.rate
            except NoRateError:
                try:
                    usd_currency = self.repository.get_currency(
                        EXCHANGE_RATE_HELPER_CUR_CODE
                    )
                except NoCurrencyError:
                    raise CantConvertError(
                        'Расчёт перевода невозможен, так как отсутствует '
                        'вспомогательная валюта, необходимая для вычисления '
                        'обменного курса'
                    )
                if usd_currency.id is not None:
                    usd_currency_id = usd_currency.id

                try:
                    rate_usd_from = self.repository.get_rate(
                        usd_currency_id, from_currency_id
                    )
                    rate_usd_to = self.repository.get_rate(
                        usd_currency_id, to_currency_id
                    )
                    rate = rate_usd_to.rate / rate_usd_from.rate
                except NoRateError:
                    raise CantConvertError(
                        'Расчёт перевода невозможен, так как отсутствуют '
                        'данные для вычисления обменного курса'
                    )

        return ExchangeDto(
            self._currency_to_dto(from_currency),
            self._currency_to_dto(to_currency),
            rate,
            amount,
            amount * rate,
        )

    @cached_property
    def repository(self) -> Repository:
        return Repository()

    def _currency_to_dto(self, currency: Currency) -> CurrencyDto:
        if currency.id is not None:
            id = currency.id
        return CurrencyDto(id, currency.full_name, currency.code, currency.sign)

    def _rate_to_dto(
        self,
        rate: Rate,
        base_currency: Currency,
        target_currency: Currency,
    ) -> RateDto:
        if rate.id is not None:
            id = rate.id
        return RateDto(
            id,
            self._currency_to_dto(base_currency),
            self._currency_to_dto(target_currency),
            rate.rate,
        )

    def _resolve_code_pair(
        self,
        code_a: str,
        code_b: str,
    ) -> CurrenciesInfo:
        try:
            currency_a = self.repository.get_currency(code_a)
            currency_b = self.repository.get_currency(code_b)
        except NoCurrencyError:
            raise

        if currency_a.id is not None and currency_b.id is not None:
            currency_a_id = currency_a.id
            currency_b_id = currency_b.id

        return CurrenciesInfo(currency_a, currency_b, currency_a_id, currency_b_id)
