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
        return self.client.userinfo()

    def get_kline(self, market, time_range="15min"):
        return {'data': self.client.kline(market, time_range)}

    def get_ticker(self, market):
        return self.client.ticker(market)

    def order(self, currency, price, amount, trade_type):
        if trade_type == 1:
            trade_type = 'buy'
        elif trade_type == 2:
            trade_type = 'sell'
        return self.client.trade(currency, trade_type, str(price), str(amount))

    def cancel_order(self, currency, order_id):
        return self.client.cancelOrder(currency, order_id)

    def get_order(self, currency, order_id):
        detail = json.loads(self.client.orderinfo(
            currency, order_id))['orders'][0]
        result = {'status': detail['status'], 'deal_amount': detail[
            'avg_price'], 'total_amount': detail['deal_amount']}
        return result


if __name__ == '__main__':

    api = OKAPI(os.environ['OK_ACCESS_KEY'],
                os.environ['OK_SERECT_KEY'])

    # print(api.get_ticker('btc_usdt'))
    print(api.get_kline('btc_usdt'))
    # print(api.query_account())
    # order = api.order('btc_usdt', 9000, 0.01, 1)
    # print(order)

    # print(api.cancel_order('btc_usdt', 348951105))
    # print(api.get_order('btc_usdt', 348951105))
