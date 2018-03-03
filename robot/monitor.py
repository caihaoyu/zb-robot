import os
import time

import talib
import numpy as np
# from robot.api.zb_api import ZBAPI
from robot.api.okex_api import OKAPI

# 每次购买的比例
TRADING_PAIRS = 10

# 购买追价比例
ALL_TRAILING_BUY = 0.3 / 100

# 卖出追价比例
ALL_TRAILING_SELL = 0.1 / 100

# 购买范围
TRAILING_BUY_LIMT = 1 / 100

# 购买RSI值
BUY_VALUE = 25

# 卖出利润
SELL_VALUE = 1 / 100

PANIC_VALUE = -3 / 100

WAIT_TIME = 10

# DCA范围
dca_percent = {
    0: -0.07,
    1: -0.1,
    2: -1
}


def RSI(kline=None):
    kline_data = [float(item[4]) for item in kline['data']]
    # print(kline_data)
    closes = np.array(kline_data)
    rsi = talib.RSI(closes)

    return rsi[-1]


BUY_STRATEGY_MAP = {'rsi': RSI}


def calculate_profit(buy, cost):
    return ((buy - cost) / cost) - (0.4 / 100)


def init_repo():
    return {
        'count': 0,
        'avg_price': 0,
        'dca': 0
    }


class Monitor(object):

    def __init__(self, market, buy_strategy='rsi',
                 sell_strategy='', repo=None):
        self.market = market
        self.buy_strategy = BUY_STRATEGY_MAP[buy_strategy]
        self.sell_strategy = sell_strategy
        self.api = OKAPI(os.environ['OK_ACCESS_KEY'],
                         os.environ['OK_SERECT_KEY'],
                         market)
        if repo is None:
            self.repo = init_repo()
            self.status = 0
        else:
            self.repo = repo
            self.status = 1
        self.balance = self.api.get_balance()

    def watch(self):
        kline = None
        ticker = self.api.get_ticker(market=self.market)
        if self.status == 0:
            time.sleep(1)
            kline = self.api.get_kline(market=self.market, time_range="15min")
            if kline:
                opt, buy = self.check_buy(
                    ticker, kline=kline, strategy=self.buy_strategy)
                if opt:
                    time.sleep(1)
                    self.buy(buy)
        else:
            opt, sell = self.check_sale(ticker)
            if opt:
                time.sleep(1)
                self.sell(sell)

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

                if profit < SELL_VALUE:
                    return False, 0
                else:
                    if profit_diff < 0:
                        high_profit = profit
                    elif profit_diff >= ALL_TRAILING_SELL:
                        print('go sell')
                        return True, buy

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
                    if TRAILING_BUY_LIMT >= percent >= ALL_TRAILING_BUY:
                        strategy_value = RSI(
                            self.api.get_kline(market=self.market,
                                               time_range="15min"))
                        if strategy_value <= BUY_VALUE:
                            return True, sell
                        else:
                            return False, 0
                    elif percent > TRAILING_BUY_LIMT:
                        return False, 0
                    else:
                        continue
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

    def check_sale(self, ticker):
        buy = float(ticker['ticker']['buy'])
        sell = float(ticker['ticker']['sell'])
        dca = dca_percent[self.repo['dca']]
        cost = self.repo['avg_price']
        profit = calculate_profit(buy, cost)
        print(f'profit:{round(profit*100, 2)}%')
        if profit >= SELL_VALUE:
            return self.follow_up(buy, profit)
        elif profit <= PANIC_VALUE:
            return True, buy
        elif profit <= dca:
            print('go dca')
            opt, sell = self.follow_down(
                sell, isdca=True, strategy=self.buy_strategy)
            if opt:
                time.sleep(1)
                self.buy(sell, isdca=True)
                return False, 0
            else:
                return False, 0
        else:
            return False, 0

    def check_buy(self, ticker, kline, strategy):
        strategy_value = strategy(kline)

        print(strategy_value)
        if strategy_value <= BUY_VALUE:
            return self.follow_down(ticker['ticker']['sell'],
                                    strategy=self.buy_strategy)
        else:
            return False, 0

    def buy(self, price, isdca=False):
        print('go_buy')
        if isdca:
            amount = (self.repo['avg_price'] * self.repo['count']) / price
        else:
            amount = float(self.balance) / price

        print(f'buy_price:{price}')
        print(f'buy_amount:{amount}')
        order = self.api.order(self.market, price, amount, 1)
        time.sleep(WAIT_TIME)
        print(order)
        if order['code'] == 1000:
            order_detail = self.api.get_order(self.market, order['id'])
            print(order_detail)
            if order_detail['status'] == 2:
                if isdca is False:
                    self.repo['count'] += order_detail['total_amount']
                    if 'avg_price' in order_detail:
                        self.repo['avg_price'] = float(
                            order_detail['avg_price'])
                    else:
                        self.repo['avg_price'] = float(
                            order_detail['trade_money']) / self.repo['count']
                else:
                    last_cost = self.repo['avg_price'] * self.repo['count']
                    total_cost = float(order_detail['trade_money']) + last_cost
                    self.repo['count'] += order_detail['total_amount']
                    self.repo['avg_price'] = total_cost / self.repo['count']
                    self.repo['dca'] += 1
                self.status = 1
                time.sleep(15 * 60)
            elif order_detail['status'] == 0:
                self.api.cancel_order(self.market, order['id'])
            print(self.repo)

    def sell(self, price):
        amount = self.repo['count'] * 0.998
        print(f'sell_price:{price}')
        print(f'sell_amount:{amount}')
        order = self.api.order(self.market, price, amount, 0)
        print(order)
        time.sleep(WAIT_TIME)
        if order['code'] == 1000:
            order_detail = self.api.get_order(self.market, order['id'])
            print(order_detail)
            if order_detail['status'] == 2:
                self.status = 0
                self.repo = init_repo()
                self.balance = self.api.get_balance()
                print(f'balance={self.balance}')
            elif order_detail['status'] == 0:
                self.api.cancel_order(self.market, order['id'])


if __name__ == '__main__':

    repo = {'count': 0.00792323288819173, 'avg_price': 11358.9997,
            'dca': 0}
    # repo = None
    monitor = Monitor('btc_usdt', 'rsi', '', repo)

    while True:
        try:
            monitor.watch()
            time.sleep(WAIT_TIME)
        except Exception as ex:
            print(ex)
            time.sleep(WAIT_TIME)
