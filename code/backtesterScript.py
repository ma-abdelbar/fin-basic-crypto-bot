from datetime import datetime
import backtrader as bt
import strategies

symbol = 'ETHUSDT'

timeframe = '5m'


pot = 100000
percentage = 10


cerebro = bt.Cerebro()
cerebroBH = bt.Cerebro()


cerebro.broker.setcash(pot)
cerebroBH.broker.setcash(pot)

cerebro.addsizer(bt.sizers.PercentSizer, percents = percentage)
cerebroBH.addsizer(bt.sizers.PercentSizer, percents = percentage)


dataname = "data/{0}-{1}.csv".format(symbol,timeframe)

fromdate = datetime.strptime('2019/02/20','%Y/%m/%d')
todate = datetime.strptime('2020/08/22','%Y/%m/%d')

compression = int(timeframe[:-1])
print(compression)


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

# data = bt.feeds.GenericCSVData(dataname="data/ETHUSDT-5m.csv", dtformat=2, compression=compression, fromdate=fromdate, todate=todate, timeframe=bt.TimeFrame.Minutes)
#data = bt.feeds.GenericCSVData(dataname='Aug21-Now-15MINUTE-BTCUSDT.csv', dtformat=2)


cerebro.adddata(data)
cerebroBH.adddata(data)
cerebroBH.addstrategy(strategies.BuyHold)
# cerebro.addstrategy(strategies.BuyHold)
# cerebro.addstrategy(strategies.BasicRSI, period=14,overbought=70,oversold=50)
cerebro.addstrategy(strategies.GoldenCross,fast=50,slow=200)

cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name = "sharpe")
cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
# cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
# cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

initial_value = cerebro.broker.getvalue()
print('Starting Portfolio Value: %.2f' % initial_value)

resultBH = cerebroBH.run()
BH_value = cerebroBH.broker.getvalue()

result = cerebro.run()

final_value = cerebro.broker.getvalue()
print('Final Portfolio Value: %.2f' % final_value)
print('Profit %.3f%%' % (((final_value - initial_value) / initial_value) * 100))
print('Buy Hold Portfolio Value: %.2f' % BH_value)
print('Buy Hold Profit %.3f%%' % (((BH_value - initial_value) / initial_value) * 100))





figure = cerebro.plot(fmt_x_ticks = '%Y-%b-%d %H:%M',
             fmt_x_data = '%Y-%b-%d %H:%M')


# figure.savefig('1.png')

