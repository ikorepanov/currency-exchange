from functools import cached_property

from currency_exchange.dtos import (
    CurrencyDto,
    ExchangeDto,
    ExchangePostDto,
    RateDto,
)
from currency_exchange.exceptions import (
    CantConvertError,
    NoCurrencyError,
    NoCurrencyPairError,
    NoRateError,
)
from currency_exchange.models import Currency, Rate
from currency_exchange.mvc_layers.repositories import CurrencyRepository, RateRepository


class Service:
    def get_currencies(self) -> list[CurrencyDto]:
        currencies = self.currency_repository.get_currencies()
        return [self._currency_to_dto(currency) for currency in currencies]

    def get_currency(self, cur_code: str) -> CurrencyDto:
        currency = self.currency_repository.get_currency(cur_code)
        return self._currency_to_dto(currency)

    def get_rates(self) -> list[RateDto]:
        rates = self.rate_repository.get_rates()
        return [
            self._rate_to_dto(
                rate,
                self.currency_repository.get_currency_by_id(rate.base_id),
                self.currency_repository.get_currency_by_id(rate.target_id),
            )
            for rate in rates
        ]

    def get_rate(self, code_pair: str) -> RateDto:
        try:
            base_currency = self.currency_repository.get_currency(code_pair[:3])
            target_currency = self.currency_repository.get_currency(code_pair[3:])
        except NoCurrencyError:
            raise NoRateError(
                'Обменный курс для пары не найден, '
                'так как не найдена одна или обе валюты'
            )
        if base_currency.id is not None and target_currency.id is not None:
            base_currency_id = base_currency.id
            target_currency_id = target_currency.id
        rate = self.rate_repository.get_rate(base_currency_id, target_currency_id)
        return self._rate_to_dto(rate, base_currency, target_currency)

    def create_currency(
        self, cur_name: str, cur_code: str, cur_sign: str
    ) -> CurrencyDto:
        currency = Currency(None, cur_code, cur_name, cur_sign)
        currency_with_id = self.currency_repository.create_currency(currency)
        return self._currency_to_dto(currency_with_id)

    def create_rate(
        self, base_cur_code: str, target_cur_code: str, rate: str
    ) -> RateDto:
        try:
            base_currency = self.currency_repository.get_currency(base_cur_code)
            target_currency = self.currency_repository.get_currency(target_cur_code)
        except NoCurrencyError:
            raise NoCurrencyPairError(
                'Одна (или обе) валюта из валютной пары не существует в БД'
            )
        if base_currency.id is not None and target_currency.id is not None:
            base_currency_id = base_currency.id
            target_currency_id = target_currency.id
        exchange_rate = Rate(None, base_currency_id, target_currency_id, float(rate))
        exchange_rate_with_id = self.rate_repository.create_rate(exchange_rate)
        return self._rate_to_dto(exchange_rate_with_id, base_currency, target_currency)

    def update_rate(self, code_pair: str, rate: str) -> RateDto:
        try:
            base_currency = self.currency_repository.get_currency(code_pair[:3])
            target_currency = self.currency_repository.get_currency(code_pair[3:])
        except NoCurrencyError:
            raise NoRateError(
                'Валютная пара отсутствует в базе данных, '
                'так как не найдена одна или обе валюты'
            )
        if base_currency.id is not None and target_currency.id is not None:
            base_currency_id = base_currency.id
            target_currency_id = target_currency.id
        exchange_rate = Rate(None, base_currency_id, target_currency_id, float(rate))
        exchange_rate_with_id = self.rate_repository.update_rate(exchange_rate)
        return self._rate_to_dto(exchange_rate_with_id, base_currency, target_currency)

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
