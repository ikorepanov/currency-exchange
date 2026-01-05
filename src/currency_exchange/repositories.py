from sqlite3 import OperationalError, connect

from currency_exchange.exceptions import CurrencyExchangeError, NoCurrencyError
from currency_exchange.models import Currency, Rate


class CurrencyRepository:
    def get_all_currencies(self) -> list[Currency]:
        return [
            Currency(row[0], row[1], row[2], row[3]) for row in self._retrieve_all()
        ]

    def get_currency_with_code(self, cur_code: str) -> Currency:
        raw_data = self._retrieve_one_with_code(cur_code)
        return Currency(raw_data[0], cur_code, raw_data[1], raw_data[2])

    def get_currency_with_id(self, cur_id: int) -> Currency:
        raw_data = self._retrieve_one_with_id(cur_id)
        return Currency(cur_id, raw_data[0], raw_data[1], raw_data[2])

    def _retrieve_all(self) -> list[tuple[int, str, str, str]]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM Currencies')
            return cur.fetchall()
        except OperationalError as error:
            raise CurrencyExchangeError(error)

    def _retrieve_one_with_code(self, cur_code: str) -> tuple[int, str, str]:
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

    def _retrieve_one_with_id(self, cur_id: int) -> tuple[str, str, str]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'SELECT Code, FullName, Sign FROM Currencies WHERE ID = ?',
                    (cur_id,),
                )
                query_result = cur.fetchone()
            if query_result is None:
                raise NoCurrencyError()
            return query_result
        except OperationalError as error:
            raise CurrencyExchangeError(error)


class RateRepository:
    def get_all_rates(self) -> list[Rate]:
        return [Rate(row[0], row[1], row[2], row[3]) for row in self._retrieve_all()]

    def _retrieve_all(self) -> list[tuple[int, int, int, float]]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM ExchangeRates')
            return cur.fetchall()
        except OperationalError as error:
            raise CurrencyExchangeError(error)
