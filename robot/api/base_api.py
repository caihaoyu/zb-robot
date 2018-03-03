from abc import ABCMeta, abstractmethod


class IAPI(metaclass=ABCMeta):

    @abstractmethod
    def query_account(self):
        pass

    @abstractmethod
    def get_kline(self, market, time_range="15min"):
        pass

    @abstractmethod
    def get_ticker(self, market):
        pass

    @abstractmethod
    def order(self, currency, price, amount, trade_type):
        pass

    @abstractmethod
    def cancel_order(self, currency, order_id):
        pass

    @abstractmethod
    def get_order(self, currency, order_id):
        pass

    @abstractmethod
    def get_balance(self, name='usdt'):
        pass
