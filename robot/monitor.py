

class Monitor(object):

    def __init__(self, market, buy_strategy, sell_strategy):
        self.market = market
        self.buy_strategy = buy_strategy
        self.sell_strategy = sell_strategy
