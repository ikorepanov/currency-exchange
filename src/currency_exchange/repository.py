from sqlite3 import OperationalError, connect

from currency_exchange.exceptions import CurrencyExchangeError, NoCurrencyError
from currency_exchange.models import Currency


class Repository:
    def retrieve_all(self) -> list[tuple[int, str, str, str]]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM Currencies')
            return cur.fetchall()
        except OperationalError as error:
            raise CurrencyExchangeError(error)

    def retrieve_one(self, cur_code: str) -> tuple[int, str, str]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'SELECT ID, FullName, Sign FROM Currencies WHERE Code = ?',
                    (cur_code,),
                )
                query_result = cur.fetchone()
            if query_result is None:
                raise NoCurrencyError()
            return query_result
        except OperationalError as error:
            raise CurrencyExchangeError(error)

    def get_all_currencies(self) -> list[Currency]:
        return [Currency(row[0], row[1], row[2], row[3]) for row in self.retrieve_all()]

    def get_one_currency(self, cur_code: str) -> Currency:
        raw_data = self.retrieve_one(cur_code)
        return Currency(raw_data[0], cur_code, raw_data[1], raw_data[2])
