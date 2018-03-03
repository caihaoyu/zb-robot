from .base_api import IAPI
import json
from ..okex.OkcoinSpotAPI import OKCoinSpot
import os


class OKAPI(IAPI):

    def __init__(self, mykey, mysecret, market=None):
        self.mykey = mykey
        self.mysecret = mysecret
        self.market = market
        url = 'www.okex.com'
        self.client = OKCoinSpot(url, self.mykey, self.mysecret)

    def query_account(self):
        return json.loads(self.client.userinfo())

    def get_balance(self, name='usdt'):
        account = self.query_account()
        return float(account['info']['funds']['free'][name])

    def get_kline(self, market, time_range="15min"):
        return {'data': self.client.kline(market, time_range)}

    def get_ticker(self, market):
        return self.client.ticker(market)

    def order(self, currency, price, amount, trade_type):
        trade_type = 'buy' if trade_type == 1 else 'sell'
        result = json.loads(self.client.trade(
            currency, trade_type, str(price), str(amount)))
        result['id'] = result['order_id']
        result['code'] = 100 if result['result'] else 500
        return result

    def cancel_order(self, currency, order_id):
        return self.client.cancelOrder(currency, order_id)

    def get_order(self, currency, order_id):
        detail = json.loads(self.client.orderinfo(
            currency, order_id))['orders'][0]
        trade_money = float(detail['avg_price']) * float(detail['deal_amount'])
        result = {'status': detail['status'],
                  'deal_amount': detail['deal_amount'],
                  'total_amount': detail['amount'],
                  'avg_price': detail['avg_price'],
                  'trade_money': trade_money
                  }
        return result


if __name__ == '__main__':

    api = OKAPI(os.environ['OK_ACCESS_KEY'],
                os.environ['OK_SERECT_KEY'])

    # print(api.get_ticker('btc_usdt'))
    # print(api.get_kline('btc_usdt'))
    account = api.query_account()

    print(api.get_balance())
    # order = api.order('btc_usdt', 19000, 0.007907386422415348, 0)
    # print(order['order_id'])

    # print(api.cancel_order('btc_usdt', 348951105))
    # print(api.get_order('btc_usdt', 348951105))
