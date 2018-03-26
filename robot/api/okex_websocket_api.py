from .base_api import IAPI
import os
import websocket
import hashlib
import zlib
import base64
import json


def on_open(self):
    self.send(
        "{'event': 'addChannel', 'channel': 'ok_sub_spot_btc_usdt_kline_15min'}")


def on_message(self, evt):
    data = json.loads(evt)
    print(data)


def inflate(data):
    decompress = zlib.decompressobj(
        -zlib.MAX_WBITS  # see above
    )
    inflated = decompress.decompress(data)
    inflated += decompress.flush()
    return inflated


def on_error(self, evt=None):
    print(evt)


def on_close(self, evt=None):
    print('DISCONNECT')


class OKAPI(object):

    def __init__(self, mykey, mysecret, market=None):
        self.mykey = mykey
        self.mysecret = mysecret
        self.market = market
        url = "wss://real.okex.com:10441/websocket"
        websocket.enableTrace(False)
        self.client = websocket.WebSocketApp(url,
                                             on_message=on_message,
                                             on_error=on_error,
                                             on_close=on_close)
        self.client.on_open = on_open
        self.client.run_forever()

    def buildMySign(params):
        sign = ''
        for key in sorted(params.keys()):
            sign += key + '=' + str(params[key]) + '&'
        sign += f'secret_key=f{self.mysecret}'
        return hashlib.md5((sign).encode("utf-8")).hexdigest().upper()

    def query_account(self):
        pass

    def get_kline(self, market, time_range="15min"):

        msg = {'event': 'addChannel',
               'channel': f'ok_sub_spot_{market}_kline_{time_range}'}
        print(msg)
        return self.client.send(msg)

    def get_ticker(self, market):
        pass

    def order(self, currency, price, amount, trade_type):
        pass

    def cancel_order(self, currency, order_id):
        pass

    def get_order(self, currency, order_id):
        pass


if __name__ == '__main__':

    api = OKAPI(os.environ['OK_ACCESS_KEY'],
                os.environ['OK_SECRET_KEY'])

    print(api.get_kline('btc_usdt'))
