from .base_api import IAPI
from ..okex.spot_api import SpotAPI
from ..okex.Account_api import AccountAPI
from ..okex.Market_api import MarketAPI
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

    def query_account(self):
        pass

    def get_balance(self, name='USDT'):
        result = self.account_client.get_account(name)
        # print(result['data'][0].get('details')[0].get('cashBal'))
        return float(result['data'][0].get('details')[0].get('cashBal'))

    def get_kline(self, market, time_range='1D'):
        # 先写死一天
        time_range = '1D'
        kline = self.market_client.get_markprice_candlesticks(market, bar=time_range)
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
        api_respnse = self.client.get_specific_ticker(market)
        result = {'ticker': {
            'buy': api_respnse['best_ask'], 'sell': api_respnse['best_bid']}}
        return result

    def order(self, currency, price, amount, trade_type):
        trade_type = 'buy' if trade_type == 1 else 'sell'
        price, amount = str(price), str(amount)
        result = self.client.take_order(
            'btc_usdt', trade_type, client_oid='',
            type='limit', price=price, order_type='0',
            notional='1', size=amount)
        result['id'] = result['order_id']
        result['code'] = 1000 if result['result'] else 500
        return result

    def cancel_order(self, currency, order_id):
        return self.client.revoke_order(currency, order_id)

    def get_order(self, currency, order_id):
        detail = self.client.get_order_info(currency, order_id)
        trade_money = float(detail['price_avg']) * float(detail['filled_size'])
        result = {'status': int(detail['state']),
                  'deal_amount': float(detail['filled_size']),
                  'total_amount': float(detail['size']),
                  'avg_price': float(detail['price_avg']),
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
    print(api.get_kline('BTC-USD-SWAP'))

    # print(api.get_order('btc_usdt', '4603346987586560'))
    # order = api.order('btc_usdt', 19000, 0.007907386422415348, 0)
    # print(order['order_id'])

    # print(api.cancel_order('btc_usdt', 348951105))
    # print(api.get_order('btc_usdt', 348951105))
