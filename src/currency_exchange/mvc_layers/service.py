from functools import cached_property

from currency_exchange.dtos import (
    CurrencyDto,
    ExchangeDto,
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

EXCHANGE_RATE_HELPER_CUR_CODE = 'PPP'


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

    def exchange_currencies(
        self, from_cur_code: str, to_cur_code: str, amount: float
    ) -> ExchangeDto:
        try:
            from_currency = self.currency_repository.get_currency(from_cur_code)
            to_currency = self.currency_repository.get_currency(to_cur_code)
        except NoCurrencyError:
            raise CantConvertError(
                'Расчёт перевода невозможен, так как не найдена одна или обе валюты'
            )
        if from_currency.id is not None and to_currency.id is not None:
            from_currency_id = from_currency.id
            to_currency_id = to_currency.id

        # 1.
        try:
            exchange_rate = self.rate_repository.get_rate(
                from_currency_id, to_currency_id
            )
            rate = exchange_rate.rate
        except NoRateError:
            # 2.
            try:
                reversed_exchange_rate = self.rate_repository.get_rate(
                    to_currency_id, from_currency_id
                )
                rate = 1 / reversed_exchange_rate.rate
            except NoRateError:
                # 3.
                try:
                    usd_currency = self.currency_repository.get_currency(
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
                    rate_usd_from = self.rate_repository.get_rate(
                        usd_currency_id, from_currency_id
                    )
                    rate_usd_to = self.rate_repository.get_rate(
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
