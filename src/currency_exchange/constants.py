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

DROP_CURRENCIES_TABLE_SQL = 'DROP TABLE IF EXISTS Currencies'

CREATE_CURRENCIES_TABLE_SQL = """
CREATE TABLE Currencies (
ID INTEGER PRIMARY KEY,
Code VARCHAR NOT NULL,
FullName VARCHAR NOT NULL,
Sign VARCHAR NOT NULL
)
"""
CREATE_UNIQUE_INDEX_CURRENCIES_SQL = """
CREATE UNIQUE INDEX
currencies_code
ON Currencies(Code)
"""

INSERT_INTO_CURRENCIES_SQL = """
INSERT OR IGNORE INTO Currencies
(Code, FullName, Sign)
VALUES (?, ?, ?)
"""

DROP_EXCHANGE_RATES_TABLE_SQL = 'DROP TABLE IF EXISTS ExchangeRates'

CREATE_EXCHANGE_RATES_TABLE_SQL = """
CREATE TABLE ExchangeRates (
ID INTEGER PRIMARY KEY,
BaseCurrencyId INTEGER NOT NULL,
TargetCurrencyId INTEGER NOT NULL,
Rate NUMERIC NOT NULL
)
"""

CREATE_UNIQUE_INDEX_EXCHANGE_RATES_SQL = """
CREATE UNIQUE INDEX
rates_base_target
ON ExchangeRates(BaseCurrencyId, TargetCurrencyId)
"""

INSERT_INTO_EXCHANGE_RATES_SQL = """
INSERT OR IGNORE INTO ExchangeRates
(BaseCurrencyId, TargetCurrencyId, Rate)
VALUES (?, ?, ?)
"""

GET_ID_FROM_CURRENCIES_SQL = """
SELECT ID
FROM Currencies
WHERE code = ?
"""
