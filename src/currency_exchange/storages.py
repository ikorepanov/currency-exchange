from sqlite3 import OperationalError, connect

from currency_exchange.exceptions import CurrencyExchangeError, NoCurrencyError
from currency_exchange.models import Currency, Rate


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


class RateStorage:
    def load_all(self) -> list[Rate]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM ExchangeRates')
                raw_data = cur.fetchall()

                result = []
                for data in raw_data:
                    id = data[0]
                    base_currency_id = data[1]
                    target_currency_id = data[2]
                    rate = data[3]

                    cur.execute(
                        'SELECT Code, FullName, Sign FROM Currencies WHERE ID = ?',
                        (base_currency_id,),
                    )
                    raw_data = cur.fetchone()
                    base_currency = Currency(
                        base_currency_id, raw_data[1], raw_data[0], raw_data[2]
                    )

                    cur.execute(
                        'SELECT Code, FullName, Sign FROM Currencies WHERE ID = ?',
                        (target_currency_id,),
                    )
                    raw_data = cur.fetchone()
                    target_currency = Currency(
                        target_currency_id, raw_data[1], raw_data[0], raw_data[2]
                    )

                    result.append(Rate(id, base_currency, target_currency, rate))
            return result
        except OperationalError as error:
            raise CurrencyExchangeError(error)
