from sqlite3 import OperationalError, connect

from currency_exchange.exceptions import CurrencyExchangeError, NoCurrencyError
from currency_exchange.models import Currency


class CurrencyStorage:
    def load_all(self) -> list[Currency]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM Currencies')
                raw_data = cur.fetchall()
            return [Currency(data[0], data[2], data[1], data[3]) for data in raw_data]
        except OperationalError as error:
            raise CurrencyExchangeError(error)

    def load_one(self, cur_code: str) -> Currency:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'SELECT ID, FullName, Sign FROM Currencies WHERE Code = ?',
                    (cur_code,),
                )
                raw_data = cur.fetchone()
            if raw_data is None:
                raise NoCurrencyError()
            return Currency(raw_data[0], raw_data[1], cur_code, raw_data[2])
        except OperationalError as error:
            raise CurrencyExchangeError(error)
