from decimal import Decimal
from pathlib import Path
from sqlite3 import connect

from loguru import logger

from currency_exchange.constants import (
    CREATE_CURRENCIES_TABLE_SQL,
    CREATE_EXCHANGE_RATES_TABLE_SQL,
    CREATE_UNIQUE_INDEX_CURRENCIES_SQL,
    CREATE_UNIQUE_INDEX_EXCHANGE_RATES_SQL,
    DROP_CURRENCIES_TABLE_SQL,
    DROP_EXCHANGE_RATES_TABLE_SQL,
    GET_ID_FROM_CURRENCIES_SQL,
    INSERT_INTO_CURRENCIES_SQL,
    INSERT_INTO_EXCHANGE_RATES_SQL,
    NUMBER_OF_DECIMAL_PLACES_FOR_RATES,
)
from currency_exchange.utils.data_helpers import round_decimal

BASE_DIR = Path(__file__).resolve().parent

file_path_db = BASE_DIR / 'db.sqlite'
file_path_currencies = BASE_DIR / 'data' / 'Currencies.csv'
file_path_exchange_rates = BASE_DIR / 'data' / 'ExchangeRates.csv'


def create_db() -> None:
    with connect(str(file_path_db)) as conn:
        cur = conn.cursor()
        cur.execute(DROP_CURRENCIES_TABLE_SQL)
        cur.execute(CREATE_CURRENCIES_TABLE_SQL)
        cur.execute(CREATE_UNIQUE_INDEX_CURRENCIES_SQL)

        with file_path_currencies.open(encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                csv_parts = line.split(',')

                code = csv_parts[0]
                name = csv_parts[1]
                sign = csv_parts[2]

                cur.execute(
                    INSERT_INTO_CURRENCIES_SQL,
                    (code, name, sign),
                )

        cur.execute(DROP_EXCHANGE_RATES_TABLE_SQL)
        cur.execute(CREATE_EXCHANGE_RATES_TABLE_SQL)
        cur.execute(CREATE_UNIQUE_INDEX_EXCHANGE_RATES_SQL)

        with file_path_exchange_rates.open(encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                csv_parts = line.split(',')

                base_cur_code = csv_parts[0]
                target_cur_code = csv_parts[1]
                rate_str = csv_parts[2]

                rate_dec = round_decimal(
                    Decimal(rate_str), NUMBER_OF_DECIMAL_PLACES_FOR_RATES
                )

                cur.execute(GET_ID_FROM_CURRENCIES_SQL, (base_cur_code,))
                base_cur_id = cur.fetchone()[0]

                cur.execute(GET_ID_FROM_CURRENCIES_SQL, (target_cur_code,))
                target_cur_id = cur.fetchone()[0]

                cur.execute(
                    INSERT_INTO_EXCHANGE_RATES_SQL,
                    (base_cur_id, target_cur_id, str(rate_dec)),
                )

        logger.info('DB with tables "Currencies" and "ExchangeRates" has just created')


if __name__ == '__main__':
    create_db()
