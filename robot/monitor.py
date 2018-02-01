import os
import time

import talib
import numpy as np
from zb_api import ZBAPI

trading_pairs = 2

BUY_VALUE = 25

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


class Monitor(object):

    def __init__(self, market, buy_strategy, sell_strategy):
        self.market = market
        self.buy_strategy = buy_strategy
        self.sell_strategy = sell_strategy
        self.api = ZBAPI(os.environ['ZB_ACCESS_KEY'],
                         os.environ['ZB_SERECT_KEY'],
                         market)
        self.repo = {
            'count': 0,
            'avg_price': 0,
            'dca': 0
        }
        self.status = 0

    def watch(self):
        kline = None
        ticker = self.api.get_ticker(market=self.market)
        if self.status == 0:
            kline = self.api.get_kline(market=self.market, time_range="5min")
            if kline:
                opt, sell = self.check_buy(ticker, RSI(kline))
                if opt:
                    self.buy(sell)
        else:
            self.check_sale(ticker)

    def follow_down(self, sell):
        lowest_sell = float(sell)
        # current_rsi = rsi

        while True:
            try:
                ticker = self.api.get_ticker(market=self.market)
                sell = float(ticker['ticker']['sell'])
                percent = (sell - lowest_sell) / lowest_sell

                print(lowest_sell, sell)

                if sell > lowest_sell:
                    if 0.01 >= percent >= 0.003:
                        close, rsi = RSI(
                            self.api.get_kline(market=self.market,
                                               time_range="15min"))
                        if rsi <= BUY_VALUE:
                            return True, sell
                        else:
                            return False, 0
                    elif percent > 0.01:
                        return False, 0
                    else:
                        continue
                else:
                    lowest_sell = sell

                time.sleep(30)
            except Exception as ex:
                print(ex)
                time.sleep(30)

    def check_sale(self, ticker):
        print(ticker)

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


if __name__ == '__main__':

    monitor = Monitor('btc_usdt', '', '')

    while True:
        try:
            monitor.watch()
            time.sleep(30)
        except Exception as ex:
            print(ex)
            time.sleep(30)
