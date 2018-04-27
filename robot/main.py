import argparse
import threading

from robot.monitor.monitor import Monitor


def run_monitor(symbol):
    monitor = Monitor(market=symbol)
    monitor.run()


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--debug', action='store_true',
                        help='Enable DEBUG message output.')

    return parser.parse_args()


def main():
    symbols = ['bch_usdt', 'eos_usdt', 'ont_usdt', 'okb_usdt']

    threads = []

    for symbol in symbols:
        thread = threading.Thread(
            target=run_monitor,
            name=symbol,
            kwargs={'symbol': symbol}
        )

        threads.append(thread)

        thread.start()


if __name__ == '__main__':
    main()
