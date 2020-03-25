import os
import time

import talib
import numpy as np
# from robot.api.zb_api import ZBAPI
from robot.api.okex_api import OKAPI
from robot.util import gram
# from robot.strategy import RSIStrategy

# # 每次购买的比例
# TRADING_PAIRS = 10

# 购买追价比例
ALL_TRAILING_BUY = 0.3 / 100

# 卖出追价比例
ALL_TRAILING_SELL = 0.1 / 100

# 购买范围
TRAILING_BUY_LIMT = 0.5 / 100

# 购买RSI值
BUY_VALUE = 28.25

# 卖出利润
SELL_VALUE = 50

PANIC_VALUE = -3 / 100

WAIT_TIME = 10

ATR = 0

# DCA范围
dca_percent = {
    0: -1,
    1: -1,
    2: -1
}


def RSI(kline=None):
    kline_data = [float(item[4]) for item in kline['data']]
    # print(kline_data)
    closes = np.array(kline_data)
    rsi = talib.RSI(closes, timeperiod=14)

    return rsi[-1]


def EMA_MACD(kline=None):
    if len(kline['data']) < 20:
        return None, None
    kline_data = [float(item[4]) for item in kline['data']]
    closes = np.array(kline_data)
    macd = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
    ema = talib.EMA(closes, timeperiod=5)
    return ema, macd


def calculate_buy(kline):
    ema, macd = EMA_MACD(kline)
    if ema is None or macd is None:
        return False
    if ema[-2] - ema[-3] > 0 and macd[2][-1] > 0:
        return True
    return False


def calculate_sell(kline):
    ema, macd = EMA_MACD(kline)
    if ema is None or macd is None:
        return False
    if ema[-2] - ema[-3] * 0.995 < 0:
        return True
    return False


BUY_STRATEGY_MAP = {'rsi': RSI, 'ema': EMA_MACD}


def calculate_profit(price, cost):
    # print(price)
    # print(cost)
    return ((price * (0.998 ** 2) - cost) / cost)


def get_ATR(day_kline):
    kline_data = [list(map(float, item)) for item in day_kline['data']]

    data = np.array(kline_data)
    ATR = talib.ATR(data[:, 2], data[:, 3], data[:, 4], timeperiod=20)
    return ATR[-1]


def init_repo():
    return {
        'count': 0,
        'avg_price': 0,
        'dca': 0
    }


def judgment_order(opt, value, order_method):
    if opt:
        order_method(value)


class Monitor(object):

    def __init__(self, market, buy_strategy='ema',
                 sell_strategy='', repo=None):
        self.market = market
        self.market_code = self.market.replace('_', '').upper()
        self.buy_strategy = BUY_STRATEGY_MAP[buy_strategy]
        self.sell_strategy = sell_strategy
        self.api = OKAPI(os.environ['OK_ACCESS_KEY'],
                         os.environ['OK_SERECT_KEY'],
                         os.environ['OK_PASSPHRASE'],
                         market)
        if repo is None:
            self.repo = init_repo()
            self.status = 0
        else:
            self.repo = repo
            self.status = 1
        self.balance = self.api.get_balance()
        self.is_loss = False
        # self.balance = 10

    def watch(self):
        kline = self.api.get_kline(market=self.market, time_range="1day")
        ticker = self.api.get_ticker(market=self.market)
        if kline:
            if self.status == 0:
                judgment_order(*self.check_buy(ticker, kline=kline), self.buy)
            else:
                judgment_order(*self.check_sale(ticker, kline=kline),
                               self.sell)

    def follow_up(self, buy, high_profit):
        cost = self.repo['avg_price']
        while True:
            try:
                time.sleep(WAIT_TIME)
                ticker = self.api.get_ticker(market=self.market)
                buy = float(ticker['ticker']['buy'])
                profit = calculate_profit(buy, cost)
                profit_diff = high_profit - profit

                print(f'profit:{profit},\n'
                      f'profit_diff:{profit_diff},\n'
                      f'high_profit:{high_profit}')

                if profit_diff < 0:
                    high_profit = profit
                elif profit_diff >= ALL_TRAILING_SELL:
                    print('go sell')
                    return True, buy

                # if profit < SELL_VALUE:
                #     return False, 0
                # else:
                #     if profit_diff < 0:
                #         high_profit = profit
                #     elif profit_diff >= ALL_TRAILING_SELL:
                #         print('go sell')
                #         return True, buy

            except Exception as ex:
                print(ex)
                time.sleep(WAIT_TIME)

    def follow_down(self, sell, strategy, isdca=False):

        lowest_sell = float(sell)
        # current_rsi = rsi

        while True:
            try:
                time.sleep(WAIT_TIME)
                ticker = self.api.get_ticker(market=self.market)
                sell = float(ticker['ticker']['sell'])
                percent = (sell - lowest_sell) / lowest_sell

                print(lowest_sell, sell)

                if sell > lowest_sell and isdca is False:
                    if percent >= ALL_TRAILING_BUY:
                        return True, sell
                elif isdca and sell > lowest_sell:
                    dca = dca_percent[self.repo['dca']]
                    cost = self.repo['avg_price']
                    profit = calculate_profit(sell, cost)
                    if TRAILING_BUY_LIMT >= percent >= ALL_TRAILING_BUY:
                        if profit <= dca:
                            return True, sell
                        else:
                            return False, 0

                else:
                    lowest_sell = sell

            except Exception as ex:
                print(ex)
                time.sleep(WAIT_TIME)

    def check_sale(self, ticker, kline):
        is_sell = calculate_sell(kline=kline)
        buy = float(ticker['ticker']['buy'])
        sell = float(ticker['ticker']['sell'])
        dca = dca_percent[self.repo['dca']]
        cost = self.repo['avg_price']
        profit = calculate_profit(buy, cost)

        print(f'profit: {round(profit*100, 2)}%')

        if is_sell:
            return self.follow_up(buy, profit)
        elif profit <= PANIC_VALUE:
            return True, buy
        elif profit <= dca:
            print('go dca')
            opt, sell = self.follow_down(
                sell, isdca=True, strategy=self.buy_strategy)
            if opt:
                self.buy(sell, isdca=True)
                return False, 0
            else:
                return False, 0
        else:
            return False, 0

    def check_buy(self, ticker, kline):
        is_buy = calculate_buy(kline)
        print(f'is_buy:{is_buy}')
        if is_buy:
            return self.follow_down(ticker['ticker']['sell'],
                                    strategy=self.buy_strategy)
        else:
            return False, 0
        # return True, float(ticker['ticker']['sell'])

    def buy(self, price, isdca=False):
        print('go_buy')
        if isdca:
            amount = (self.repo['avg_price'] * self.repo['count']) / price
        else:
            amount = float(self.balance) / price

        print(f'buy_price:{price}')
        print(f'buy_amount:{amount}')
        order = self.api.order(self.market, price, amount, 1)
        time.sleep(60)
        print(order)
        if order['code'] == 1000:
            order_detail = self.api.get_order(self.market, order['id'])
            print(order_detail)
            if order_detail['status'] == 2:
                last_cost = self.repo['avg_price'] * self.repo['count']
                total_cost = float(order_detail['trade_money']) + last_cost
                self.repo['count'] += order_detail['total_amount']
                self.repo['avg_price'] = total_cost / self.repo['count']
                if isdca:
                    self.repo['dca'] += 1
                self.status = 1
                gram.send_trade_message(trade_type='buy',
                                        market=self.market_code,
                                        amaout=self.repo['count'],
                                        rate=self.repo['avg_price'],
                                        trade_money=order_detail['trade_money']
                                        )
                print(self.repo)
                time.sleep(15 * 60)
            elif order_detail['status'] == 0:
                self.api.cancel_order(self.market, order['id'])
            else:
                self.api.cancel_order(self.market, order['id'])
                order_detail = self.api.get_order(self.market, order['id'])
                last_cost = self.repo['avg_price'] * self.repo['count']
                total_cost = float(order_detail['trade_money']) + last_cost
                # 这个地方需要计算成交的值
                self.repo['count'] += order_detail['deal_amount']
                self.repo['avg_price'] = total_cost / self.repo['count']
                self.balance -= order_detail['trade_money']
                price = self.api.get_ticker['sell']
                self.buy(price=price)
            print(self.repo)

    def sell(self, price):
        amount = self.repo['count'] * 0.998
        print(f'sell_price:{price}')
        print(f'sell_amount:{amount}')
        order = self.api.order(self.market, price, amount, 0)
        print(order)
        time.sleep(60)
        if order['code'] == 1000:
            order_detail = self.api.get_order(self.market, order['id'])
            print(order_detail)
            if order_detail['status'] == 2:
                self.status = 0
                profit = calculate_profit(
                    order_detail['avg_price'], self.repo['avg_price'])
                balance = self.api.get_balance()
                old_repo = self.repo
                self.repo = init_repo()
                gram.send_trade_message(trade_type='sell',
                                        market=self.market_code,
                                        profit=f'{round(profit*100, 2)}%',
                                        amaout=order_detail['total_amount'],
                                        cost=old_repo['avg_price'],
                                        rate=order_detail['avg_price'],
                                        balance=balance
                                        )
                print(f'balance={balance}')
                self.balance = balance
                time.sleep(24 * 60 * 60)
            elif order_detail['status'] == 0:
                self.api.cancel_order(self.market, order['id'])
            else:
                self.api.cancel_order(self.market, order['id'])
                order_detail = self.api.get_order(self.market, order['id'])
                self.repo['count'] -= order_detail['deal_amount']
                price = self.api.get_ticker['buy']
                self.sell(price=price)


if __name__ == '__main__':
    import traceback
    repo = {'count': 1.75507759, 'avg_price': 6229, 'dca': 0}
    # repo = None
    monitor = Monitor('btc_usdt', 'rsi', '', repo)

    while True:
        try:
            monitor.watch()
            time.sleep(WAIT_TIME)
        except Exception as ex:
            traceback.print_exc()
            time.sleep(WAIT_TIME)
