from .base_api import IAPI
from ..okex.spot_api import SpotAPI
from ..okex.account_api import AccountAPI
from ..okex.Market_api import MarketAPI
from ..okex.Trade_api import TradeAPI
import os


class OKAPI(IAPI):

    def __init__(self, mykey, mysecret, passphrase, market=None):
        self.mykey = mykey
        self.mysecret = mysecret
        self.market = market
        self.passphrase = passphrase

        self.account_client = AccountAPI(self.mykey, self.mysecret,
                                         self.passphrase, False)

        self.market_client = MarketAPI(self.mykey, self.mysecret,
                                       self.passphrase, False)

        self.trade_client = TradeAPI(self.mykey, self.mysecret,
                                     self.passphrase, False)

    def query_account(self):
        pass

    def get_balance(self, name='USDT'):
        result = self.account_client.get_account(name)
        # print(result['data'][0].get('details')[0].get('cashBal'))
        return float(result['data'][0].get('details')[0].get('cashBal'))

    def get_kline(self, market, time_range='1D'):
        # 先写死一天
        time_range = '1D'
        kline = self.market_client.get_markprice_candlesticks(market, bar=time_range)[
            'data']
        return {'data': kline[::-1]}

    def get_ticker(self, market):
        '''
        # Response
        okex v1 接口返回
        {
            "date":"1410431279",
            "ticker":{
                "buy":"33.15",
                "high":"34.15",
                "last":"33.15",
                "low":"32.05",
                "sell":"33.16",
                "vol":"10532696.39199642"
            }
        }
        '''
        api_respnse = self.market_client.get_ticker(market)['data'][0]
        result = {'ticker': {
            'buy': api_respnse['askPx'], 'sell': api_respnse['bidPx']}}
        return result

    def order(self, currency, price, amount, trade_type):
        # trade_type = 'buy' if trade_type == 1 else 'sell'
        price, amount = str(price), str(amount)
        result = self.trade_client.place_order(
            'BTC-USDT', 'cash', trade_type, 'limit', amount, '', '', '', '', price)
        # result = self.client.take_order(
        #     'btc_usdt', trade_type, client_oid='',
        #     type='limit', price=price, order_type='0',
        #     notional='1', size=amount)
        result['id'] = result['data'][0]['ordId']
        result['code'] = 1000 if result['code'] == 0 else 500
        return result

    def cancel_order(self, currency, order_id):
        return self.trade_client.cancel_order(currency, order_id)

    def get_order(self, currency, order_id):
        detail = self.trade_client.get_orders(
            currency, order_id, '')['data'][0]
        print(detail)
        if detail['avgPx'] == '':
            detail['avgPx'] = 0
        # detail = self.client.get_order_info(currency, order_id)
        trade_money = float(detail['avgPx']) * float(detail['fillSz'])
        if detail['state'] == 'live':
            detail['state'] = 0
        if detail['state'] == 'filled':
            detail['state'] = 2
        if detail['state'] == 'partially_filled':
            detail['state'] = 1

        result = {'status': int(detail['state']),
                  'deal_amount': float(detail['fillSz']),
                  'total_amount': float(detail['sz']),
                  'avg_price': float(detail['avgPx']),
                  'trade_money': trade_money
                  }
        return result


if __name__ == '__main__':
    print(os.environ['OK_ACCESS_KEY'])

    api = OKAPI(os.environ['OK_ACCESS_KEY'],
                os.environ['OK_SERECT_KEY'],
                os.environ['OK_PASSPHRASE'])

    # print(api.get_ticker('btc_usdt'))
    # print(api.order('btc_usdt', 0.1, 1, 'buy'))

    account = api.query_account()
    # print(api.cancel_order('btc_usdt', '4611768738255873'))
    print(api.get_balance())
    # print(api.get_kline('BTC-USDT'))
    # print(api.get_ticker('BTC-USDT'))
    # print(api.order('btc_usdt', 0.1, 1, 'buy'))

    # print(api.get_order('btc_usdt', '4603346987586560'))
    # order = api.order('btc_usdt', 19000, 0.007907386422415348, 0)
    # print(order['order_id'])

    # print(api.cancel_order('BTC-USDT', 340532908133871617))
    # print(api.get_order('BTC-USDT', 340532908133871617))
