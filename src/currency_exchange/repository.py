from sqlite3 import OperationalError, connect

from currency_exchange.exceptions import CurrencyExchangeError
from currency_exchange.models import Currency


class Repository:
    def retrieve_data(self) -> list[tuple[int, str, str, str]]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM Currencies')
                query_result = cur.fetchall()
            return query_result
        except OperationalError as error:
            raise CurrencyExchangeError(error)

    def get_all_currencies(self) -> list[Currency]:
        return [
            Currency(row[0], row[1], row[2], row[3]) for row in self.retrieve_data()
        ]
