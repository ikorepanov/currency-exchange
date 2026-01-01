from sqlite3 import OperationalError, connect

from currency_exchange.exceptions import CurrencyExchangeError
from currency_exchange.models import Currency


class CurrencyStorage:
    def read(self) -> list[Currency]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM Currencies')
                raw_data = cur.fetchall()
            return [Currency(data[0], data[2], data[1], data[3]) for data in raw_data]
        except OperationalError as error:
            raise CurrencyExchangeError(error)
