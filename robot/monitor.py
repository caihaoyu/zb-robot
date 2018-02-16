import os
import time

import talib
import numpy as np
from zb_api import ZBAPI

trading_pairs = 2

ALL_TRAILING_BUY = 0.001

ALL_TRAILING_SELL = 0.0001

TRAILING_BUY_LIMT = 1

BUY_VALUE = 100

SELL_VALUE = 0.01

dca_percent = {
    1: -0.07,
    2: -0.1,
    3: -0.24
}


def RSI(kline=None):
    kline_data = kline['data']

    closes = np.array(kline_data)[:, 4]
    rsi = talib.RSI(closes)

    return closes[-1], rsi[-1]


def init_repo():
    return {
        'count': 0,
        'avg_price': 0,
        'dca': 0
    }


class Monitor(object):

    def __init__(self, market, buy_strategy, sell_strategy, repo=None):
        self.market = market
        self.buy_strategy = buy_strategy
        self.sell_strategy = sell_strategy
        self.api = ZBAPI(os.environ['ZB_ACCESS_KEY'],
                         os.environ['ZB_SERECT_KEY'],
                         market)
        if repo is None:
            self.repo = init_repo()
            self.status = 0
        else:
            self.repo = repo
            self.status = 1

    def watch(self):
        kline = None
        ticker = self.api.get_ticker(market=self.market)
        if self.status == 0:
            kline = self.api.get_kline(market=self.market, time_range="5min")
            if kline:
                opt, buy = self.check_buy(ticker, RSI(kline))
                if opt:
                    self.buy(buy)
        else:
            opt, sell = self.check_sale(ticker)
            if opt:
                self.sell(sell)

    def follow_up(self, buy, high_profit):
        cost = self.repo['avg_price']
        while True:
            try:
                time.sleep(30)
                ticker = self.api.get_ticker(market=self.market)
                buy = float(ticker['ticker']['buy'])
                profit = (buy - cost) / cost
                profit_diff = high_profit - profit

                print(f'profit:{profit},\nprofit_diff:{profit_diff},\nhigh_profit:{high_profit}')

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
                time.sleep(30)

    def follow_down(self, sell):

        lowest_sell = float(sell)
        # current_rsi = rsi

        while True:
            try:
                time.sleep(30)
                ticker = self.api.get_ticker(market=self.market)
                sell = float(ticker['ticker']['sell'])
                percent = (sell - lowest_sell) / lowest_sell

                print(lowest_sell, sell)

                if sell > lowest_sell:
                    if TRAILING_BUY_LIMT >= percent >= ALL_TRAILING_BUY:
                        close, rsi = RSI(
                            self.api.get_kline(market=self.market,
                                               time_range="15min"))
                        if rsi <= BUY_VALUE:
                            return True, sell
                        else:
                            return False, 0
                    elif percent > TRAILING_BUY_LIMT:
                        return False, 0
                    else:
                        continue
                else:
                    lowest_sell = sell

            except Exception as ex:
                print(ex)
                time.sleep(30)

    def check_sale(self, ticker):
        buy = float(ticker['ticker']['buy'])
        cost = self.repo['avg_price']
        profit = (buy - cost) / cost
        print(f'profit:{round(profit*100, 2)}%')
        if profit >= SELL_VALUE:
            return self.follow_up(buy, profit)
        else:
            return False, 0

    def check_buy(self, ticker, rsi_value=None):
        close, rsi = rsi_value

        print(rsi)
        if rsi <= BUY_VALUE:
            return self.follow_down(ticker['ticker']['sell'])
        else:
            return False, 0

    def buy(self, price, dca=0):
        print('go_buy')
        amount = float(trading_pairs) // price

        print(f'buy_price:{price}')
        print(f'buy_amount:{amount}')
        order = self.api.order(self.market, price, amount, 1)
        time.sleep(30)
        if order['code'] == 1000:
            order_detail = self.api.get_order(self.market, order['id'])
            print(order_detail)
            self.repo['count'] += order_detail['total_amount']
            if order_detail['status'] == 2:
                if dca == 0:
                    self.repo['avg_price'] = float(
                        order_detail['trade_money']) / self.repo['count']
                self.status = 1
            elif order_detail['status'] == 0:
                pass
            print(self.repo)

    def sell(self, price):
        amount = self.repo['count']
        print(f'sell_price:{price}')
        print(f'sell_amount:{amount}')
        order = self.api.order(self.market, price, amount, 0)
        print(order)
        time.sleep(30)
        if order['code'] == 1000:
            order_detail = self.api.get_order(self.market, order['id'])
            print(order_detail)
            if order_detail['status'] == 2:
                self.status = 0
                self.repo = init_repo()
            elif order_detail['status'] == 0:
                pass


if __name__ == '__main__':

    repo = {'count': 1.0, 'avg_price': 1.1473, 'dca': 0}
    monitor = Monitor('zb_usdt', '', '', repo)

    while True:
        try:
            monitor.watch()
            time.sleep(30)
        except Exception as ex:
            print(ex)
            time.sleep(30)
