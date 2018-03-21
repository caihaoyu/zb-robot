import talib
import numpy as np


class RSIStrategy(object):

    # 每次购买的比例
    # TRADING_PAIRS = 10

    # 购买追价比例
    ALL_TRAILING_BUY = 0.3 / 100

    # 卖出追价比例
    ALL_TRAILING_SELL = 0.1 / 100

    # 购买范围
    TRAILING_BUY_LIMT = 0.5 / 100

    # 购买RSI值
    BUY_VALUE = 28.25

    # 卖出利润
    SELL_VALUE = 50

    PANIC_VALUE = -3 / 100

    ATR = 0

    # DCA范围
    DCA_TRIGGER = {
        0: -0.07,
        1: -0.1,
        2: -1
    }

    @staticmethod
    def RSI(kline=None):
        kline_data = [float(item[4]) for item in kline['data']]
        # print(kline_data)
        closes = np.array(kline_data)
        rsi = talib.RSI(closes, timeperiod=14)

        return rsi[-1]
