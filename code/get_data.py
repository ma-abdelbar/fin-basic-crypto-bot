import config, csv
import os
from binance.client import Client
from datetime import datetime

import ccxt
from datetime import datetime

# OPTION 1

client = Client(config.API_KEY, config.API_SECRET)


historic_path = r'../historic_data'
#
# symbol = r'ETHUSDT'
COIN_TARGETS = ["BTC", "AVAX"]#["ETH","FIL", "ADA","BTC"]
COIN_REFER = "USDT"
targets = [("1m", "Jan22"), ("5m", "Jun21"), ("30m", "Jan19"), ("1h", "Jan17"), ("1d", "Jan14")]

for COIN_TARGET in COIN_TARGETS:
    symbol = COIN_TARGET + COIN_REFER

    for target in targets:
        timeframe = target[0]
        start_date = target[1]


        csvname ='{0}-{1}.csv'.format(COIN_TARGET+COIN_REFER,timeframe)
        csvnamedt ='{0}-{1}-dt.csv'.format(COIN_TARGET+COIN_REFER,timeframe)


        klines_date = "1 {0}, 20{1}".format(start_date[:-2], start_date[-2:])
        csvpath = os.path.join(historic_path,csvname)
        csvpathdt = os.path.join(historic_path,csvnamedt)

        print(csvpath)

        csvfile = open(csvpath, 'w', newline='')
        csvfiledt = open(csvpathdt, 'w', newline='')


        candlestick_writer = csv.writer(csvfile, delimiter=',')
        candlestick_writerdt = csv.writer(csvfiledt, delimiter=',')


        candlesticks = client.get_historical_klines(symbol, timeframe, klines_date)

        for candlestick in candlesticks:
            candlestick[0] = candlestick[0] / 1000
            candlestick_writer.writerow(candlestick)
            unix_val = datetime.fromtimestamp(candlestick[0])
            candlestick[0] = unix_val
            candlestick_writerdt.writerow(candlestick)
        csvfile.close()
        csvfiledt.close()








#
