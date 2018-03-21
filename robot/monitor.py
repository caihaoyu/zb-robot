import threading
from threading import Lock

from robot.common import util
from robot.monitor.monitor import Monitor

balance = util.current_balance()


def get_local_balance(lock):
    try:
        if lock.acquire(blocking=False):
            global balance
            return balance
        return False
    except Exception as e:
        print(e)


def update_local_balance(lock, change):
    try:
        lock.acquire(blocking=True)
        global balance
        balance += change
        lock.release()
    except Exception as e:
        print(e)


def run_monitor(symbol, balance, lock):
    monitor = Monitor(market=symbol, lock=lock, balance=balance)
    monitor.run()


def main():
    symbols = ['ltc_usdt', 'etc_usdt', 'bch_usdt']

    threads = []
    lock = Lock()

    for symbol in symbols:
        thread = threading.Thread(
            target=run_monitor,
            name=symbol,
            kwargs={
                'symbol': symbol,
                'lock': lock,
                'balance': balance,
                'get_local_balance': get_local_balance,
                'update_local_balance': update_local_balance,
            })

        threads.append(thread)

        thread.start()


if __name__ == '__main__':
    main()
