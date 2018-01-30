__author__ = 'Ziyang'

import json
import hashlib
import struct
import time
import sys
import urllib.request


class zb_api:

    def __init__(self, mykey, mysecret):
        self.mykey = mykey
        self.mysecret = mysecret
        self.jm = ''

    def __fill(self, value, lenght, fillByte):
        if len(value) >= lenght:
            return value
        else:
            fillSize = lenght - len(value)
        return value + chr(fillByte) * fillSize

    def __doXOr(self, s, value):
        slist = list(s.decode('utf-8'))
        for index in range(len(slist)):
            slist[index] = chr(ord(slist[index]) ^ value)
        return "".join(slist)

    def __hmacSign(self, aValue, aKey):
        keyb = struct.pack("%ds" % len(aKey), aKey.encode('utf-8'))
        value = struct.pack("%ds" % len(aValue), aValue.encode('utf-8'))
        k_ipad = self.__doXOr(keyb, 0x36)
        k_opad = self.__doXOr(keyb, 0x5c)
        k_ipad = self.__fill(k_ipad, 64, 54)
        k_opad = self.__fill(k_opad, 64, 92)
        m = hashlib.md5()
        m.update(k_ipad.encode('utf-8'))
        m.update(value)
        dg = m.digest()

        m = hashlib.md5()
        m.update(k_opad.encode('utf-8'))
        subStr = dg[0:16]
        m.update(subStr)
        dg = m.hexdigest()
        return dg

    def __digest(self, aValue):
        value = struct.pack("%ds" % len(aValue), aValue.encode('utf-8'))
        print(value)
        h = hashlib.sha1()
        h.update(value)
        dg = h.hexdigest()
        return dg

    def __api_call(self,
                   path,
                   params='',
                   base_url='https://trade.zb.com/api/'):
        try:
            SHA_secret = self.__digest(self.mysecret)
            sign = self.__hmacSign(params, SHA_secret)
            self.jm = sign
            reqTime = (int)(time.time() * 1000)
            params += '&sign=%s&reqTime=%d' % (sign, reqTime)
            url = f'{base_url}' + path + '?' + params
            req = urllib.request.Request(url)
            res = urllib.request.urlopen(req, timeout=2)
            doc = json.loads(res.read())
            return doc
        except Exception as ex:
            print(sys.stderr, 'zb request ex: ', ex)
            return None

    def __data_api_call(self, path, params, base_url='https://trade.zb.com/api/'):
        pass

    def query_account(self):
        try:
            params = "accesskey=" + self.mykey + "&method=getAccountInfo"
            path = 'getAccountInfo'

            obj = self.__api_call(path, params)
            # print obj
            return obj
        except Exception as ex:
            print(sys.stderr, 'zb query_account exception,', ex)
            return None

    def get_kline(self, market, time_range="5min"):
        params = f"market={market}&type={time_range}"
        path = "kline"
        base_url = "http://api.zb.com/data/v1/"
        obj = self.__api_call(path, params, base_url)
        return obj

    def get_ticker(self, market):
        params = f"market={market}"
        path = "ticker"
        base_url = "http://api.zb.com/data/v1/"
        obj = self.__api_call(path, params, base_url)
        return obj

    def order(self, currency, price, amount, trade_type):
        params = (f"accesskey={self.mykey}&amount={amount}&currency={currency}"
                  f"&method=order&price={price}"
                  f"&tradeType={trade_type}")
        path = "order"
        return self.__api_call(path, params)

    def cancel_order(self, currency, order_id):
        params = (f"accesskey={self.mykey}&currency={currency}"
                  f"&id={order_id}&method=cancelOrder")
        path = "cancelOrder"
        return self.__api_call(path, params)

    def get_order(self, currency, order_id):
        params = (f"accesskey={self.mykey}&currency={currency}"
                  "&id={order_id}&method=getOrder")
        path = "getOrder"
        return self.__api_call(path, params)


if __name__ == '__main__':

    api = zb_api(access_key, access_secret)

    # print(api.query_account())
    #
    print(api.get_kline("bts_usdt", time_range="15min"))
    #
    # print(api.get_ticker("bts_usdt"))

    # print(api.order("bts_usdt", 0.4127, 4, 1))

    # print(api.get_order("bts_usdt", 201801295784546))
    # print(api.cancel_order("bts_usdt", 201801295784546))
