def init_repo():
    return {
        'count': 0,
        'avg_price': 0,
        'dca': 0,
        'stop_lose': 0
    }


def calculate_profit(price, cost):
    # print(price)
    # print(cost)
    return ((price * (0.998 ** 2) - cost) / cost)
