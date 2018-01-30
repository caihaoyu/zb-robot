import os
import time

import talib
import numpy as np
from zb_api import ZBAPI


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
        self.stats = 0

    def watch(self):
        kline = None
        if self.stats == 0:
            kline = self.api.get_kline(market=self.market, time_range="5min")

        ticker = self.api.get_ticker(market=self.market)
        print(ticker)

        if kline:
            opt, sell = self.check_buy(ticker, RSI(kline))
            if opt:
                self.buy(sell)

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
                                               time_range="5min"))
                        if rsi <= 25:
                            return True, sell
                        else:
                            return False, 0
                    elif percent > 0.01:
                        return False, 0
                    else:
                        continue
                else:
                    lowest_sell = sell

                time.sleep(5)
            except Exception as ex:
                print(ex)
                time.sleep(5)

    def check_sale(self, ticker):
        pass

    def check_buy(self, ticker, rsi_value=None):
        close, rsi = rsi_value

        if rsi <= 25:
            return self.follow_down(ticker['ticker']['sell'])
        else:
            return False, 0

    def buy(self, ticker):
        self.stats = 1
        # count = amount // price

        # if count > 0:
        #     base -= count * price
        #     repo['avg_price'] = update_avg_price(repo, count, price)
        #     repo['count'] += count

        #     print('BUY:    {}'.format(int(count)))
        #     print('PRICE:  {}'.format(price))
        #     print('AMOUNT: {}'.format(count * price))
        #     print('BASE:   {}'.format(base))
        #     print('REPO:   {}'.format(repo))


if __name__ == '__main__':

    monitor = Monitor('bts_usdt', '', '')

    while True:
        try:
            monitor.watch()
            time.sleep(5)
        except Exception as ex:
            print(ex)
            time.sleep(5)
