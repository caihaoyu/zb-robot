import time

import talib
import numpy as np

from robot import env
# from robot.api.zb_api import ZBAPI
from robot.api.okex_api import OKAPI
from robot.common import gram, util
from robot.strategy.rsi import RSIStrategy


BUY_STRATEGY_MAP = {'rsi': RSIStrategy.RSI}

WAIT_TIME = 10


def get_ATR(day_kline):
    kline_data = [list(map(float, item)) for item in day_kline['data']]

    data = np.array(kline_data)
    ATR = talib.ATR(data[:, 2], data[:, 3], data[:, 4], timeperiod=20)
    return ATR[-1]


def judgment_order(opt, value, order_method):
    if opt:
        order_method(value)


class Monitor(object):

    def __init__(self, market, buy_strategy='rsi',
                 sell_strategy='', repo=None, lock=None):
        self.market = market
        self.market_code = self.market.replace('_', '').upper()
        self.buy_strategy = BUY_STRATEGY_MAP[buy_strategy]
        self.sell_strategy = sell_strategy
        self.api = OKAPI(env.OK_ACCESS_KEY,
                         env.OK_SECRET_KEY,
                         market)
        if repo is None:
            self.repo = util.init_repo()
            self.status = 0
        else:
            self.repo = repo
            self.status = 1
        self.balance = self.api.get_balance() * 0.5
        self.is_loss = False
        self.lock = lock
        # self.balance = 10

    def watch(self):
        kline = self.api.get_kline(market=self.market, time_range="15min")
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
                profit = util.calculate_profit(buy, cost)
                profit_diff = high_profit - profit

                print(f'profit:{profit},\n'
                      f'profit_diff:{profit_diff},\n'
                      f'high_profit:{high_profit}')

                if profit_diff < 0:
                    high_profit = profit
                elif profit_diff >= RSIStrategy.ALL_TRAILING_SELL:
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
                    if percent >= RSIStrategy.ALL_TRAILING_BUY:
                        strategy_value = RSIStrategy.RSI(
                            self.api.get_kline(market=self.market,
                                               time_range="15min"))
                        if strategy_value <= RSIStrategy.BUY_VALUE:
                            return True, sell
                        else:
                            return False, 0
                elif isdca and sell > lowest_sell:
                    dca = RSIStrategy.DCA_TRIGGER[self.repo['dca']]
                    cost = self.repo['avg_price']
                    profit = util.calculate_profit(sell, cost)
                    if (percent <= RSIStrategy.TRAILING_BUY_LIMT and
                       percent >= RSIStrategy.ALL_TRAILING_BUY):
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
        rsi = RSIStrategy.RSI(kline=kline)
        buy = float(ticker['ticker']['buy'])
        sell = float(ticker['ticker']['sell'])
        dca = RSIStrategy.DCA_TRIGGER[self.repo['dca']]
        cost = self.repo['avg_price']
        profit = util.calculate_profit(buy, cost)

        print(f'profit: {round(profit*100, 2)}%, RSI:{rsi}')

        if (profit > 0 and rsi >= RSIStrategy.SELL_VALUE) or profit > 0.15:
            return self.follow_up(buy, profit)
        elif profit <= RSIStrategy.PANIC_VALUE:
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
        strategy_value = self.buy_strategy(kline)

        print(f'RSI:{strategy_value}')
        if strategy_value <= RSIStrategy.BUY_VALUE:
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
                self.balance -= order_detail['trade_money']
                price = self.api.get_ticker['sell']
                self.sell(price=price)
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
                profit = util.calculate_profit(
                    order_detail['avg_price'], self.repo['avg_price'])
                balance = self.api.get_balance()
                old_repo = self.repo
                self.repo = util.init_repo()
                gram.send_trade_message(trade_type='sell',
                                        market=self.market_code,
                                        profit=f'{round(profit*100, 2)}%',
                                        amaout=order_detail['total_amount'],
                                        cost=old_repo['avg_price'],
                                        rate=order_detail['avg_price'],
                                        balance=balance
                                        )
                print(f'balance={balance}')
                self.balance = balance if self.is_loss else balance * 0.5

                if profit > 0:
                    self.balance = balance * 0.5
                    self.is_loss = False
                else:
                    self.is_loss = True
                # time.sleep(15 * 60)
            elif order_detail['status'] == 0:
                self.api.cancel_order(self.market, order['id'])
            else:
                self.api.cancel_order(self.market, order['id'])
                order_detail = self.api.get_order(self.market, order['id'])
                self.repo['count'] -= order_detail['deal_amount']
                price = self.api.get_ticker['buy']
                self.sell(price=price)

    def run(self):
        while True:
            try:
                self.watch()
                time.sleep(WAIT_TIME)
            except Exception as ex:
                print(ex)
                time.sleep(WAIT_TIME)


if __name__ == '__main__':
    # repo = {'count':0.04636555 , 'avg_price':8749.1008, 'dca': 0}
    repo = None
    monitor = Monitor('btc_usdt', 'rsi', '', repo)