import math
import backtrader as bt
from datetime import datetime
from termcolor import colored
from settings import (
    PRODUCTION, DEVELOPMENT, ENV, COIN_TARGET, COIN_REFER, SYMBOL, TIMEFRAMES,
    PERCENTAGE, BACKTEST_CASH, DEBUG, SANDBOX
)

class StrategyBase(bt.Strategy):
    def __init__(self):
        self.order = None
        self.last_operation = "SELL"
        self.status = "DISCONNECTED"
        self.bar_executed = 0
        self.buy_price_close = None
        self.soft_sell = False                  # What is this:
        self.hard_sell = False                  # What is this:
        self.log("Base strategy initialized")

    def log(self, txt, color=None):
        if not DEBUG:
            return
        value = datetime.now()
        if len(self) > 0:
            value = self.data.datetime.datetime()

        if color:
            txt = colored(txt, color)
        print('[%s] %s' % (value.strftime("%d-%m-%y %H:%M"), txt))


    def reset_sell_indicators(self):
        self.soft_sell = False
        self.hard_sell = False
        self.buy_price_close = None

    def notify_data(self, data, status, *args, **kwargs):
        '''Receives a notification from data'''
        self.status = data._getstatusname(status)
        # print(self.status)
        if status == data.LIVE:
            print("LIVE DATA - Ready to trade")
            #self.log("LIVE DATA - Ready to trade")

    def short(self):
        if self.last_operation == "SELL":
            return
        if ENV == DEVELOPMENT:
            self.log("Sell ordered: $%.2f" % self.data.close[0])
            return self.sell()
        cash, value = self.broker.get_wallet_balance(COIN_TARGET)
        self.log("Sell ordered: $%.2f. Amount %.6f %s - $%.2f USDT" % (self.data.close[0],
                                                                       self.position.size, COIN_TARGET, value))
        return self.close()


    def long(self):
        if self.last_operation == "BUY":
            return

        self.log("Buy ordered: $%.2f" % self.data.close[0])
        self.buy_price_close = self.data.close[0]
        price = self.data.close[0]

        if ENV == DEVELOPMENT:
            return self.buy()

        cash, value = self.broker.get_wallet_balance(COIN_REFER)
        self.log("Buy ordered: $%.2f. Amount %.6f %s. Ballance $%.2f USDT" % (self.data.close[0],
                                                                              self.getsizing(), COIN_TARGET, value))
        return self.buy()



    def myclose(self):
        if self.last_operation == "SELL":
            return
        if ENV == DEVELOPMENT:
            self.log("Sell ordered: $%.2f" % self.data.close[0])
            return self.sell()
        cash, value = self.broker.get_wallet_balance(COIN_TARGET)
        self.log("Sell ordered: $%.2f. Amount %.6f %s - $%.2f USDT" % (self.data.close[0],
                                                                       self.position.size, COIN_TARGET, value))
        return self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log('ORDER ACCEPTED/SUBMITTED')
            self.order = order
            return

        if order.status in [order.Expired]:
            self.log('BUY EXPIRED', True)

        elif order.status in [order.Completed]:
            if order.isbuy():
                self.last_operation = "BUY"
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                if ENV == PRODUCTION:
                    print(order.__dict__)

            else:  # Sell
                self.last_operation = "SELL"
                self.reset_sell_indicators()
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            # Sentinel to None: new orders allowed
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected: Status %s - %s' % (order.Status[order.status],
                                                                         self.last_operation))

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        color = 'green'
        if trade.pnl < 0:
            color = 'red'

        self.log(colored('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm), color))


class DoNothing(StrategyBase):

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using the Do Nothing strategy")

    def next(self):
        if self.status != "LIVE" and ENV == PRODUCTION:  # waiting for live status in production
            return

        if self.order:  # waiting for pending order
            return


class BuyHold(StrategyBase):

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using BuyHold strategy")
    def next(self):

        if self.status != "LIVE" and ENV == PRODUCTION:  # waiting for live status in production
            return

        if self.order:  # waiting for pending order
            return

        if self.last_operation != "BUY":
            self.long()



class BasicRSI(StrategyBase):
    params = (('period', 14),('overbought',70),('oversold',30))

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using BasicRSI strategy")
        # self.rsi = bt.talib.RSI(self.data, timeperiod=self.params.period)
        self.rsi = bt.indicators.RelativeStrengthIndex(self.data,period=self.params.period)

    def next(self):

        if self.status != "LIVE" and ENV == PRODUCTION:  # waiting for live status in production
            return
        if self.order:  # waiting for pending order
            return

        if not self.position:
            if self.rsi < self.params.oversold:
                self.long()
        if self.position:
            if self.rsi > self.params.overbought:
                self.short()



class GoldenCross(StrategyBase):

    params = (('fast', 50), ('slow', 200))

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using GoldenCross strategy")
        fastname = '{}MA'.format(self.params.fast)
        slowname = '{}MA'.format(self.params.slow)
        self.fast_moving_average = bt.indicators.SMA(
            self.data.close, period=self.params.fast)#, plotname= fastname)
        self.slow_moving_average = bt.indicators.SMA(
            self.data.close, period=self.params.slow)#, plotname=slowname)

        self.crossover = bt.indicators.CrossOver(self.fast_moving_average, self.slow_moving_average)
    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.long()
        if self.position:
            if self.crossover < 0:
                self.short()


class RSI_EMA(StrategyBase):
    params = (('period_ema_fast', 10), ('period_ema_slow', 100))

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using RSI/EMA strategy")

        self.ema_fast = bt.indicators.EMA(period=self.params.period_ema_fast)
        self.ema_slow = bt.indicators.EMA(period=self.params.period_ema_slow)
        self.rsi = bt.indicators.RelativeStrengthIndex()

    def next(self):
        if self.status != "LIVE" and ENV == PRODUCTION:  # waiting for live status in production
            return

        if self.order:  # waiting for pending order
            return

        if not self.position:
            if self.rsi < 30 and self.ema_fast > self.ema_slow:
                self.long()

        if self.position:
            if self.rsi > 70:
                self.short()


class xRSI_GCross(StrategyBase):
    params = (('RSIperiod', 14), ('overbought', 70), ('oversold', 30),('FMAperiod', 50), ('SMAperiod',200),('tol', 0.05))

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using the RSI_GCross strategy")
        self.rsi0 = bt.indicators.RelativeStrengthIndex(self.data,period=self.params.RSIperiod)
        self.fast_moving_average = bt.indicators.SMA(self.data.close, period=self.params.FMAperiod)
        self.slow_moving_average = bt.indicators.SMA(self.data.close, period=self.params.SMAperiod)


    def next(self):
        if self.status != "LIVE" and ENV == PRODUCTION:  # waiting for live status in production
            return

        if self.order:  # waiting for pending order
            return

        ratio  = self.fast_moving_average[0] / self.slow_moving_average[0]
        trend = ['uptrend' if ratio > 1+self.params.tol else 'downtrend' if ratio < 1-self.params.tol else 'steady'][0]

        if trend == 'steady':
            # Perform BASIC RSI based on short timeframe
            if not self.position:
                if self.rsi0 < self.params.oversold:
                    self.long()
            if self.position:
                if self.rsi0 > self.params.overbought:
                    self.short()

        elif trend == 'uptrend':
            if not self.position:
                self.long()
        else: # 'downtrend'
            if self.position:
                self.short()

