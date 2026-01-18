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
)
from currency_exchange.utils.decimal_helper import to_decimal


def create_db() -> None:
    with connect('./src/currency_exchange/db/db.sqlite') as conn:
        cur = conn.cursor()
        cur.execute(DROP_CURRENCIES_TABLE_SQL)
        cur.execute(CREATE_CURRENCIES_TABLE_SQL)
        cur.execute(CREATE_UNIQUE_INDEX_CURRENCIES_SQL)

        with Path('./src/currency_exchange/db/data/Currencies.csv').open() as handle:
            for line in handle:
                csv_parts = line.strip().split(',')

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

        with Path('./src/currency_exchange/db/data/ExchangeRates.csv').open() as handle:
            for line in handle:
                csv_parts = line.strip().split(',')

                base_cur_code = csv_parts[0]
                target_cur_code = csv_parts[1]
                rate_str = csv_parts[2]

                rate_dec = to_decimal(rate_str)

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
