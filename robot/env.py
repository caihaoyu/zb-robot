import os

from robot.api.okex_api import OKAPI


OK_ACCESS_KEY = os.environ['OK_ACCESS_KEY']
OK_SECRET_KEY = os.environ['OK_SECRET_KEY']


balance = OKAPI(OK_ACCESS_KEY, OK_SECRET_KEY, 'btc_usdt').get_balance()
print(f'current balance = {balance}')
