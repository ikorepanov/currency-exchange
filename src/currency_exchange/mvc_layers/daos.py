from sqlite3 import IntegrityError, OperationalError, connect

from currency_exchange.exceptions import (
    CurrencyAlreadyExistsError,
    NoCurrencyError,
    NoDataBaseConnectionError,
    NoRateError,
    RateAlreadyExistsError,
)


class CurrencyDao:
    def create_one(self, code: str, name: str, sign: str) -> int:
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
            raise NoDataBaseConnectionError('База данных недоступна')
        except IntegrityError:
            raise CurrencyAlreadyExistsError('Валюта с таким кодом уже существует')

    def retrieve_all(self) -> list[tuple[int, str, str, str]]:
        try:
            with connect('./src/currency_exchange/db/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM Currencies')
            return cur.fetchall()
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')

    def retrieve_one(self, cur_code: str) -> tuple[int, str, str]:
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

    def retrieve_one_by_id(self, cur_id: int) -> tuple[str, str, str]:
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
            raise NoDataBaseConnectionError('База данных недоступна')


class RateDao:
    def create_one(self, base_id: int, target_id: int, rate: float) -> int:
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
            raise NoDataBaseConnectionError('База данных недоступна')
        except IntegrityError:
            raise RateAlreadyExistsError('Валютная пара с таким кодом уже существует')

    def retrieve_all(self) -> list[tuple[int, int, int, float]]:
        try:
            with connect('./src/currency_exchange/db/db.sqlite') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM ExchangeRates')
            return cur.fetchall()
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')

    def retrieve_one(
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

    def update_one(self, base_id: int, target_id: int, rate: float) -> int:
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
                raise NoRateError('Валютная пара отсутствует в базе данных')
            return query_result[0]
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')
