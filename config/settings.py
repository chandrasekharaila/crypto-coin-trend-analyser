# config/settings.py
#BTC/USDT
#ATA/USDT
#LISTA/USDT
#ARPA/USDT

SYMBOL = "BTC/USDT"
EXCHANGE = "binance"

TIMEFRAMES = ["4h","1h", "15m", "5m"]

DATA_DIRECTORY = "data"

# Default fetch limits (initial pull)
INITIAL_FETCH_LIMIT = 1500

# Incremental update limit
UPDATE_FETCH_LIMIT = 500