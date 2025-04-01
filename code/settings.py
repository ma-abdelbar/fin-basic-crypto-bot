import os

# === Environment Modes ===
PRODUCTION = "production"
DEVELOPMENT = "development"
ENV = os.getenv("ENVIRONMENT", DEVELOPMENT)  # Can be overridden via environment variable

# === Trading Config ===
COIN_TARGET = 'ETH'
COIN_REFER = 'USDT'
SYMBOL = COIN_TARGET + COIN_REFER
TIMEFRAMES = ['5m']
PERCENTAGE = 10
BACKTEST_CASH = 100
DEBUG = True
SANDBOX = True  # Use Binance testnet if True