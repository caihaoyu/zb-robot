import os
import telegram

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
    bot.send_message(chat_id=chat_id,
                     text=text,
                     parse_mode=telegram.ParseMode.MARKDOWN)


def send_sell_message(**kwargs):
    text = template_sell.format_map(kwargs)
    send_message(text)


def send_buy_message(**kwargs):
    text = template_buy.format_map(kwargs)
    send_message(text)


if __name__ == '__main__':

    sell_test = {
        'market': 'btc_usdt'.replace('_', '').upper(),
        'profit': '1%',
        'rate': 11290,
        'cost': 11300,
        'amaout': 0.1622231

    }

    send_sell_message(**sell_test)
