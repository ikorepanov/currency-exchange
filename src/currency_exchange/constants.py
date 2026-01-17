EXCHANGE_RATE_HELPER_CUR_CODE = 'USD'

CREATE_CURRENCY_SQL = """
INSERT INTO Currencies
(Code, FullName, Sign)
VALUES (?, ?, ?)
"""

GET_CURRENCIES_SQL = """
SELECT *
FROM Currencies
"""

GET_CURRENCY_BY_CODE_SQL = """
SELECT ID, FullName, Sign
FROM Currencies
WHERE Code = ?
"""

GET_CURRENCY_BY_ID_SQL = """
SELECT Code, FullName, Sign
FROM Currencies
WHERE ID = ?
"""

CREATE_EXCHANGE_RATE_SQL = """
INSERT INTO ExchangeRates
(BaseCurrencyId, TargetCurrencyId, Rate)
VALUES (?, ?, ?)
"""

GET_EXCHANGE_RATES_SQL = """
SELECT *
FROM ExchangeRates
"""

GET_EXCHANGE_RATE_SQL = """
SELECT ID, Rate
FROM ExchangeRates
WHERE BaseCurrencyId = ? AND TargetCurrencyId = ?
"""

UPDATE_EXCHANGE_RATE_SQL = """
UPDATE ExchangeRates
SET Rate = ?
WHERE BaseCurrencyId = ? AND TargetCurrencyId = ?
"""

GET_LAST_CREATED_ID_SQL = 'SELECT last_insert_rowid()'

GET_LAST_UPDATED_ID_SQL = """
SELECT ID
FROM ExchangeRates
WHERE BaseCurrencyId = ? AND TargetCurrencyId = ?
"""
