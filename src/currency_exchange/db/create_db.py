from collections.abc import Callable
from pathlib import Path
from sqlite3 import Cursor, connect
from typing import Any

from loguru import logger


def create_db_at(path: str) -> None:
    with connect(path) as conn:
        cur = conn.cursor()
        create_tables(cur)
        fill_tables(cur)
        logger.info('DB with tables "Currencies" and "ExchangeRates" has just created')


def create_tables(cur: Cursor) -> None:
    cur.execute('DROP TABLE IF EXISTS Currencies')
    cur.execute(
        'CREATE TABLE Currencies '
        '(ID INTEGER PRIMARY KEY, Code VARCHAR, FullName VARCHAR, Sign VARCHAR)'
    )
    cur.execute('CREATE UNIQUE INDEX currencies_code ON Currencies(Code)')

    cur.execute('DROP TABLE IF EXISTS ExchangeRates')
    cur.execute(
        'CREATE TABLE ExchangeRates '
        '(ID INTEGER PRIMARY KEY, BaseCurrencyId INTEGER, '
        'TargetCurrencyId INTEGER, Rate DECIMAL(6))'
    )
    cur.execute(
        'CREATE UNIQUE INDEX rates_base_target '
        'ON ExchangeRates(BaseCurrencyId, TargetCurrencyId)'
    )


def fill_tables(cur: Cursor) -> None:
    fill_csv_file(
        './src/currency_exchange/data/Currencies.csv', cur, insert_into_currencies
    )
    fill_csv_file(
        './src/currency_exchange/data/ExchangeRates.csv', cur, insert_into_rates
    )


def fill_csv_file(
    path: str, cur: Cursor, raw_handler: Callable[[Cursor, list[Any]], None]
) -> None:
    with Path(path).open() as handle:
        for line in handle:
            parts = line.strip().split(',')
            raw_handler(cur, parts)


def insert_into_currencies(cur: Cursor, parts: list[Any]) -> None:
    cur.execute(
        'INSERT OR IGNORE INTO Currencies (Code, FullName, Sign) VALUES (?, ?, ?)',
        (parts[0], parts[1], parts[2]),
    )


def insert_into_rates(cur: Cursor, parts: list[Any]) -> None:
    cur.execute(
        'INSERT OR IGNORE INTO ExchangeRates '
        '(BaseCurrencyId, TargetCurrencyId, Rate) VALUES (?, ?, ?)',
        (get_code_id(cur, parts[0]), get_code_id(cur, parts[1]), parts[2]),
    )


def get_code_id(cur: Cursor, code: str) -> int:
    cur.execute('SELECT ID FROM Currencies WHERE code = ?', (f'{code}',))
    return cur.fetchone()[0]


if __name__ == '__main__':
    create_db_at('./src/currency_exchange/db.sqlite')
