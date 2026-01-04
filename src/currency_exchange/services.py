from currency_exchange.models import Rate
from currency_exchange.storages import CurrencyStorage, RateStorage


class RateService:
    rate_storage = RateStorage()
    currency_storage = CurrencyStorage()

    def load_all_rates(self) -> list[Rate]:
        return [
            Rate(
                rate.id,
                self.rate_storage.load_currency_with_id(rate.base_currency_id),
                self.rate_storage.load_currency_with_id(rate.target_currency_id),
                rate.rate,
            )
            for rate in self.rate_storage.load_all_rates()
        ]
