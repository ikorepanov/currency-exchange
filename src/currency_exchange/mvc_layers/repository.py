from decimal import Decimal
from functools import cached_property

from currency_exchange.models import Currency, Rate
from currency_exchange.mvc_layers.daos import CurrencyDao, RateDao


class Repository:
    def get_currencies(self) -> list[Currency]:
        query_result = self.currency_dao.retrieve_all()
        return [Currency(row[0], row[1], row[2], row[3]) for row in query_result]

    def get_currency(self, cur_code: str) -> Currency:
        query_result = self.currency_dao.retrieve_one_by_code(cur_code)
        return Currency(query_result[0], cur_code, query_result[1], query_result[2])

    def get_currency_by_id(self, cur_id: int) -> Currency:
        query_result = self.currency_dao.retrieve_one_by_id(cur_id)
        return Currency(cur_id, query_result[0], query_result[1], query_result[2])

    def create_currency(self, currency: Currency) -> Currency:
        query_result = self.currency_dao.create_one(
            currency.code, currency.full_name, currency.sign
        )
        currency.id = query_result
        return currency

    def get_rates(self) -> list[Rate]:
        query_result = self.rate_dao.retrieve_all()
        return [Rate(row[0], row[1], row[2], Decimal(row[3])) for row in query_result]

    def get_rate(self, base_currency_id: int, target_currency_id: int) -> Rate:
        query_result = self.rate_dao.retrieve_one(base_currency_id, target_currency_id)
        return Rate(
            query_result[0],
            base_currency_id,
            target_currency_id,
            Decimal(query_result[1]),
        )

    def create_rate(self, rate: Rate) -> Rate:
        query_result = self.rate_dao.create_one(
            rate.base_id, rate.target_id, str(rate.rate)
        )
        rate.id = query_result
        return rate

    def update_rate(self, rate: Rate) -> Rate:
        query_result = self.rate_dao.update_one(
            rate.base_id, rate.target_id, str(rate.rate)
        )
        rate.id = query_result
        return rate

    @cached_property
    def currency_dao(self) -> CurrencyDao:
        return CurrencyDao()

    @cached_property
    def rate_dao(self) -> RateDao:
        return RateDao()
