import argparse
import logging
import threading
from threading import Lock

import robot.env
from robot.env import balance
from robot.monitor.monitor import Monitor


def get_local_balance(lock):
    try:
        if lock.acquire(blocking=False):
            global balance
            return balance
        return False
    except Exception as e:
        logging.error(str(e))
    finally:
        lock.release()


def update_local_balance(lock, change):
    try:
        lock.acquire(blocking=True)
        global balance
        logging.debug(f'balance: {balance}, change: {change}')
        balance += change
        lock.release()
    except Exception as e:
        logging.error(str(e))
    finally:
        lock.release()


def run_monitor(symbol,
                balance,
                lock,
                get_local_balance,
                update_local_balance):
    monitor = Monitor(market=symbol,
                      lock=lock,
                      balance=balance,
                      get_local_balance=get_local_balance,
                      update_local_balance=update_local_balance)
    monitor.run()


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--debug', action='store_true',
                        help='Enable DEBUG message output.')

    return parser.parse_args()


def main():
    args = parse_args()

    level = logging.INFO
    filename = 'info'
    if args.debug:
        level = logging.DEBUG
        filename = 'debug'

    logging.basicConfig(filename=f'log/{filename}.log',
                        level=level,
                        format='%(asctime)s - %(levelname)s - %(message)s')

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
