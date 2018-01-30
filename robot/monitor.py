from zb_api import ZBAPI
import time

class Monitor(object):

    def __init__(self, market, buy_strategy, sell_strategy):
        self.market = market
        self.buy_strategy = buy_strategy
        self.sell_strategy = sell_strategy
        self.api = ZBAPI(access_key, access_secret, market)
        self.stats = 0

    def watch(self):
        kline = None
        if self.stats == 0:
            kline = self.api.get_kline(market=self.market, time_range="5min")

        ticker = self.api.get_ticker(market=self.market)
        print(ticker)
        if self.check_buy(ticker, rsi(kline)):
            self.buy(ticker)

    def check_buy(self, ticker, rsi_value=None):
        return True

    def buy(self, ticker):
        self.stats = 1
        print('buy')


def rsi(kline=None):
    return True


if __name__ == '__main__':

    monitor = Monitor('bts_usdt', '', '')

    while True:
        try:
            monitor.watch()
            time.sleep(30)
        except Exception as ex:
            print(ex)
            time.sleep(30)
