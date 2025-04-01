import datetime
import backtrader as bt
import strategies, config
from ccxtbt import CCXTStore
import time, os
from settings import (
    PRODUCTION, DEVELOPMENT, ENV, COIN_TARGET, COIN_REFER, SYMBOL, TIMEFRAMES,
    PERCENTAGE, BACKTEST_CASH, DEBUG, SANDBOX
)
historic_path = '../historic_data'

def main():
    cerebro = bt.Cerebro(quicknotify=True)

    if ENV == PRODUCTION:  # Live trading with Binance
        broker_config = {
            'apiKey': config.API_KEY,
            'secret': config.API_SECRET,
            'nonce': lambda: str(int(time.time() * 1000)),
            'enableRateLimit': True,
        }

        store = CCXTStore(exchange='binance', currency=COIN_REFER, config=broker_config, sandbox=SANDBOX, retries=5, debug=DEBUG)

        broker_mapping = {
            'order_types': {
                bt.Order.Market: 'market',
                bt.Order.Limit: 'limit',
                bt.Order.Stop: 'stop-loss',
                bt.Order.StopLimit: 'stop limit'
            },
            'mappings': {
                'closed_order': {
                    'key': 'status',
                    'value': 'closed'
                },
                'canceled_order': {
                    'key': 'status',
                    'value': 'canceled'
                }
            }
        }
        print('Setting broker')
        broker = store.getbroker(broker_mapping=broker_mapping)
        cerebro.setbroker(broker)
        print('Getting historic data')
        hist_start_date = datetime.datetime.utcnow() - datetime.timedelta(minutes=30000)

        for timeframe in TIMEFRAMES:
            compression = int(timeframe[:-1])
            if 'm' in timeframe[-1:]:
                data = store.getdata(dataname='{0}/{1}'.format(COIN_TARGET, COIN_REFER),name=SYMBOL,timeframe=bt.TimeFrame.Minutes,fromdate=hist_start_date,compression=compression,ohlcv_limit=99999)
            elif 'd' in timeframe[-1:]:
                data = store.getdata(dataname='{0}/{1}'.format(COIN_TARGET, COIN_REFER),name=SYMBOL,timeframe=bt.TimeFrame.Days,fromdate=hist_start_date,compression=compression,ohlcv_limit=99999)
            elif 'M' in timeframe[-1:]:
                data = store.getdata(dataname='{0}/{1}'.format(COIN_TARGET, COIN_REFER),name=SYMBOL,timeframe=bt.TimeFrame.Months,fromdate=hist_start_date,compression=compression,ohlcv_limit=99999)
            else:
                data = store.getdata(dataname='{0}/{1}'.format(COIN_TARGET, COIN_REFER),name=SYMBOL,timeframe=bt.TimeFrame.Minutes,fromdate=hist_start_date,compression=60,ohlcv_limit=99999)

            # Add the feed
            cerebro.adddata(data)

    else:
        cerebroBH = bt.Cerebro()
        cerebro.broker.setcash(BACKTEST_CASH)
        cerebroBH.broker.setcash(BACKTEST_CASH)
        cerebroBH.addsizer(bt.sizers.PercentSizer, percents = PERCENTAGE)
        # cerebro.broker.setcommission(commission=0.001, name=COIN_TARGET)  # Simulating exchange fee
        # cerebroBH.broker.setcommission(commission=0.001, name=COIN_TARGET)  # Simulating exchange fee


        fromdate = datetime.datetime.strptime('2019/08/22','%Y/%m/%d')
        todate = datetime.datetime.strptime('2021/08/22','%Y/%m/%d')

        for timeframe in TIMEFRAMES:
            compression = int(timeframe[:-1])
            dataname = "{0}/{1}-{2}.csv".format(historic_path, SYMBOL, timeframe)
            if 'm' in timeframe[-1:]:
                data = bt.feeds.GenericCSVData(dataname=dataname, dtformat=2, compression=compression, fromdate=fromdate,
                                               todate=todate, timeframe=bt.TimeFrame.Minutes)
            elif 'd' in timeframe[-1:]:
                data = bt.feeds.GenericCSVData(dataname=dataname, dtformat=2, compression=compression, fromdate=fromdate,
                                               todate=todate, timeframe=bt.TimeFrame.Days)
            elif 'M' in timeframe[-1:]:
                data = bt.feeds.GenericCSVData(dataname=dataname, dtformat=2, compression=compression, fromdate=fromdate,
                                               todate=todate, timeframe=bt.TimeFrame.Months)
            else:
                data = bt.feeds.GenericCSVData(dataname=dataname, dtformat=2, compression=60, fromdate=fromdate,
                                               todate=todate,timeframe=bt.TimeFrame.Minutes)

            cerebro.adddata(data)
            cerebroBH.adddata(data)

        cerebroBH.addstrategy(strategies.BuyHold)
        resultBH = cerebroBH.run()
        BH_value = cerebroBH.broker.getvalue()

    cerebro.addsizer(bt.sizers.PercentSizer, percents=PERCENTAGE)

    # cerebro.addstrategy(strategies.RSI_GCross, RSIperiod=14, overbought=70, oversold=30,
    #                     FMAperiod=50, SMAperiod=200, tol = 0.005)
    # cerebro.addstrategy(strategies.BuyHold)
    cerebro.addstrategy(strategies.BasicRSI, period=14,overbought=70,oversold=30)
    # cerebro.addstrategy(strategies.RSI_EMA)
    # cerebro.addstrategy(strategies.GoldenCross)

    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    # cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    # cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

    initial_value = cerebro.broker.getvalue()
    print("Trading with {0}".format(initial_value * PERCENTAGE/100))
    result = cerebro.run()
    final_value = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % initial_value)
    print('Final Portfolio Value: %.2f' % final_value)
    print('Profit %.3f%%' % (((final_value - initial_value) / initial_value) * 100))
    if ENV != PRODUCTION:
        print('Buy Hold Portfolio Value: %.2f' % BH_value)
        print('Buy Hold Profit %.3f%%' % (((BH_value - initial_value) / initial_value) * 100))
    if DEBUG:
        cerebro.plot(fmt_x_ticks = '%Y-%b-%d %H:%M',
                     fmt_x_data = '%Y-%b-%d %H:%M')


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("Finished with error: ", err)
        raise