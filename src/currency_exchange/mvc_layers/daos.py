from sqlite3 import Cursor, IntegrityError, OperationalError, connect
from typing import Any

from currency_exchange.constants import (
    CREATE_CURRENCY_SQL,
    CREATE_EXCHANGE_RATE_SQL,
    GET_CURRENCIES_SQL,
    GET_CURRENCY_BY_CODE_SQL,
    GET_CURRENCY_BY_ID_SQL,
    GET_EXCHANGE_RATE_SQL,
    GET_EXCHANGE_RATES_SQL,
    GET_LAST_CREATED_ID_SQL,
    GET_LAST_UPDATED_ID_SQL,
    UPDATE_EXCHANGE_RATE_SQL,
)
from currency_exchange.exceptions import (
    CurrencyAlreadyExistsError,
    NoCurrencyError,
    NoDataBaseConnectionError,
    NoRateError,
    RateAlreadyExistsError,
)


class Dao:
    def interact_with_db(self, queries: dict[str, Any], all: bool = False) -> Any:
        with connect('./src/currency_exchange/db/db.sqlite') as conn:
            cur = conn.cursor()
            for sql, params in queries.items():
                self._execute(cur, sql, params)
        return cur.fetchall() if all else cur.fetchone()

    def _execute(self, cur: Cursor, sql: str, params: tuple[Any] | None) -> None:
        cur.execute(sql, params) if params is not None else cur.execute(sql)


class CurrencyDao(Dao):
    def create_one(self, code: str, name: str, sign: str) -> int:
        queries = {
            CREATE_CURRENCY_SQL: (code, name, sign),
            GET_LAST_CREATED_ID_SQL: None,
        }
        try:
            query_result = self.interact_with_db(queries)
            return query_result[0]
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')
        except IntegrityError:
            raise CurrencyAlreadyExistsError('Валюта с таким кодом уже существует')

    def retrieve_all(self) -> list[tuple[int, str, str, str]]:
        queries = {
            GET_CURRENCIES_SQL: None,
        }
        try:
            query_result = self.interact_with_db(queries, all=True)
            return query_result
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')

    def retrieve_one_by_code(self, cur_code: str) -> tuple[int, str, str]:
        queries = {
            GET_CURRENCY_BY_CODE_SQL: (cur_code,),
        }
        try:
            query_result = self.interact_with_db(queries)
            if query_result is None:
                raise NoCurrencyError('Валюта не найдена')
            return query_result
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')

    def retrieve_one_by_id(self, cur_id: int) -> tuple[str, str, str]:
        queries = {
            GET_CURRENCY_BY_ID_SQL: (cur_id,),
        }
        try:
            query_result = self.interact_with_db(queries)
            if query_result is None:
                raise NoCurrencyError(f'Валюта с id {cur_id} не найдена')
            return query_result
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')


class RateDao(Dao):
    def create_one(self, base_id: int, target_id: int, rate: str) -> int:
        queries = {
            CREATE_EXCHANGE_RATE_SQL: (base_id, target_id, rate),
            GET_LAST_CREATED_ID_SQL: None,
        }
        try:
            query_result = self.interact_with_db(queries)
            return query_result[0]
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')
        except IntegrityError:
            raise RateAlreadyExistsError('Валютная пара с таким кодом уже существует')

    def retrieve_all(self) -> list[tuple[int, int, int, str]]:
        queries = {
            GET_EXCHANGE_RATES_SQL: None,
        }
        try:
            query_result = self.interact_with_db(queries, all=True)
            return query_result
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')

    def retrieve_one(
        self, base_currency_id: int, target_currency_id: int
    ) -> tuple[int, str]:
        queries = {
            GET_EXCHANGE_RATE_SQL: (base_currency_id, target_currency_id),
        }
        try:
            query_result = self.interact_with_db(queries)
            if query_result is None:
                raise NoRateError('Обменный курс для пары не найден')
            return query_result
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')

    def update_one(self, base_id: int, target_id: int, rate: str) -> int:
        queries = {
            UPDATE_EXCHANGE_RATE_SQL: (rate, base_id, target_id),
            GET_LAST_UPDATED_ID_SQL: (base_id, target_id),
        }
        try:
            query_result = self.interact_with_db(queries)
            if query_result is None:
                raise NoRateError('Валютная пара отсутствует в базе данных')
            return query_result[0]
        except OperationalError:
            raise NoDataBaseConnectionError('База данных недоступна')
