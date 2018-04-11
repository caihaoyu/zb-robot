import os
import telegram
from threading import Thread

template_sell = '''
*OKEX BOT*
Just sold:{market}
**Profit**: {profit}
Rate: {rate}
Cost: {cost}
Amaout: {amaout}
Balance: {balance}
'''

template_buy = '''
*OKEX BOT*
Just bought:{market}
Rate: {rate}
Amaout: {amaout}
Trade Money: {trade_money}
'''

token = os.environ['TELEGRAM_TOKEN']
chat_id = os.environ['TELEGRAM_CHAT_ID']
bot = telegram.Bot(token=token)


def send_message(text):
    kwargs = {'chat_id': chat_id,
              'text': text,
              'parse_mode': telegram.ParseMode.MARKDOWN
              }
    # Thread(target=bot.send_message, kwargs=kwargs).start()
    return bot.send_message(**kwargs)


def send_trade_message(trade_type='sell', **kwargs):
    template = template_sell if trade_type == 'sell' else template_buy
    text = template.format_map(kwargs)
    send_message(text)


if __name__ == '__main__':

    sell_test = {
        'market': 'btc_usdt'.replace('_', '').upper(),
        'profit': '1%',
        'rate': 11290,
        'cost': 11300,
        'amaout': 0.1622231,
        'balance': 1231
    }

    # Thread(target=send_sell_message, kwargs=sell_test).start()
    send_trade_message(**sell_test)
