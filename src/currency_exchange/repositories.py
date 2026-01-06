from sqlite3 import IntegrityError, OperationalError, connect

from currency_exchange.exceptions import (
    CurrencyAlreadyExistsError,
    CurrencyExchangeError,
    NoCurrencyError,
    NoRateError,
)
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

    def save_currency(self, currency: Currency) -> Currency:
        currency.id = self._save_one(currency.code, currency.full_name, currency.sign)
        return currency

    def _save_one(self, code: str, name: str, sign: str) -> int:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'INSERT INTO Currencies (Code, FullName, Sign) VALUES (?, ?, ?)',
                    (code, name, sign),
                )
                cur.execute('SELECT last_insert_rowid()')
            return cur.fetchone()[0]
        except OperationalError as error:
            raise CurrencyExchangeError(error)
        except IntegrityError:
            raise CurrencyAlreadyExistsError

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

    def get_rate_with_cur_ids(
        self, base_currency_id: int, target_currency_id: int
    ) -> Rate:
        raw_data = self._retrieve_one_with_cur_ids(base_currency_id, target_currency_id)
        return Rate(
            raw_data[0],
            base_currency_id,
            target_currency_id,
            raw_data[1],
        )

    def _retrieve_all(self) -> list[tuple[int, int, int, float]]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM ExchangeRates')
            return cur.fetchall()
        except OperationalError as error:
            raise CurrencyExchangeError(error)

    def _retrieve_one_with_cur_ids(
        self, base_currency_id: int, target_currency_id: int
    ) -> tuple[int, float]:
        try:
            with connect('./src/currency_exchange/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'SELECT ID, Rate FROM ExchangeRates '
                    'WHERE BaseCurrencyId = ? AND TargetCurrencyId = ?',
                    (base_currency_id, target_currency_id),
                )
                query_result = cur.fetchone()
            if query_result is None:
                raise NoRateError()
            return query_result
        except OperationalError as error:
            raise CurrencyExchangeError(error)
