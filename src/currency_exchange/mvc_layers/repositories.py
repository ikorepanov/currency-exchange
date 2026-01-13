from sqlite3 import IntegrityError, OperationalError, connect

from currency_exchange.exceptions import (
    CurrencyAlreadyExistsError,
    NoCurrencyError,
    NoCurrencyPairError,
    NoDataBaseConnectionError,
    NoRateError,
    RateAlreadyExistsError,
)
from currency_exchange.models import Currency, Rate


class CurrencyRepository:
    def get_currencies(self) -> list[Currency]:
        query_result = self._retrieve_all()
        return [Currency(row[0], row[1], row[2], row[3]) for row in query_result]

    def get_currency(self, cur_code: str) -> Currency:
        query_result = self._retrieve_one(cur_code)
        return Currency(query_result[0], cur_code, query_result[1], query_result[2])

    def get_currency_by_id(self, cur_id: int) -> Currency:
        query_result = self._retrieve_one_by_id(cur_id)
        return Currency(cur_id, query_result[0], query_result[1], query_result[2])

    def save_currency(self, currency: Currency) -> Currency:
        currency.id = self._save_one(currency.code, currency.full_name, currency.sign)
        return currency

    def _save_one(self, code: str, name: str, sign: str) -> int:
        try:
            with connect('./src/currency_exchange/db/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'INSERT INTO Currencies (Code, FullName, Sign) VALUES (?, ?, ?)',
                    (code, name, sign),
                )
                cur.execute('SELECT last_insert_rowid()')
            return cur.fetchone()[0]
        except OperationalError:
            raise NoDataBaseConnectionError
        except IntegrityError:
            raise CurrencyAlreadyExistsError

    def _retrieve_all(self) -> list[tuple[int, str, str, str]]:
        try:
            with connect('./src/currency_exchange/db/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM Currencies')
            return cur.fetchall()
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')

    def _retrieve_one(self, cur_code: str) -> tuple[int, str, str]:
        try:
            with connect('./src/currency_exchange/db/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'SELECT ID, FullName, Sign FROM Currencies WHERE Code = ?',
                    (cur_code,),
                )
                query_result = cur.fetchone()
            if query_result is None:
                raise NoCurrencyError('Валюта не найдена')
            return query_result
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')

    def _retrieve_one_by_id(self, cur_id: int) -> tuple[str, str, str]:
        try:
            with connect('./src/currency_exchange/db/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'SELECT Code, FullName, Sign FROM Currencies WHERE ID = ?',
                    (cur_id,),
                )
                query_result = cur.fetchone()
            if query_result is None:
                raise NoCurrencyError()
            return query_result
        except OperationalError:
            raise NoDataBaseConnectionError


class RateRepository:
    def get_rates(self) -> list[Rate]:
        query_result = self._retrieve_all()
        return [Rate(row[0], row[1], row[2], row[3]) for row in query_result]

    def get_rate(self, base_currency_id: int, target_currency_id: int) -> Rate:
        raw_data = self._retrieve_one(base_currency_id, target_currency_id)
        return Rate(
            raw_data[0],
            base_currency_id,
            target_currency_id,
            raw_data[1],
        )

    def save_rate(self, rate: Rate) -> Rate:
        rate.id = self._save_one(rate.base_id, rate.target_id, rate.rate)
        return rate

    def update_rate(self, rate: Rate) -> Rate:
        rate.id = self._update_one(rate.base_id, rate.target_id, rate.rate)
        return rate

    def _save_one(self, base_id: int, target_id: int, rate: float) -> int:
        try:
            with connect('./src/currency_exchange/db/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'INSERT INTO ExchangeRates '
                    '(BaseCurrencyId, TargetCurrencyId, Rate) VALUES (?, ?, ?)',
                    (base_id, target_id, rate),
                )
                cur.execute('SELECT last_insert_rowid()')
            return cur.fetchone()[0]
        except OperationalError:
            raise NoDataBaseConnectionError
        except IntegrityError:
            raise RateAlreadyExistsError

    def _retrieve_all(self) -> list[tuple[int, int, int, float]]:
        try:
            with connect('./src/currency_exchange/db/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM ExchangeRates')
            return cur.fetchall()
        except OperationalError:
            raise NoDataBaseConnectionError

    def _retrieve_one(
        self, base_currency_id: int, target_currency_id: int
    ) -> tuple[int, float]:
        try:
            with connect('./src/currency_exchange/db/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'SELECT ID, Rate FROM ExchangeRates '
                    'WHERE BaseCurrencyId = ? AND TargetCurrencyId = ?',
                    (base_currency_id, target_currency_id),
                )
                query_result = cur.fetchone()
            if query_result is None:
                raise NoRateError('Обменный курс для пары не найден')
            return query_result
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')

    def _update_one(self, base_id: int, target_id: int, rate: float) -> int:
        try:
            with connect('./src/currency_exchange/db/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute(
                    'UPDATE ExchangeRates SET Rate = ? '
                    'WHERE BaseCurrencyId = ? AND TargetCurrencyId = ?',
                    (rate, base_id, target_id),
                )
                cur.execute(
                    'SELECT ID FROM ExchangeRates '
                    'WHERE BaseCurrencyId = ? AND TargetCurrencyId = ?',
                    (base_id, target_id),
                )
                query_result = cur.fetchone()
            if query_result is None:
                raise NoCurrencyPairError()
            return query_result[0]
        except OperationalError:
            raise NoDataBaseConnectionError
