import pywaves as pw
import requests
from datetime import datetime
import time


WAVES_ID = ''
USDN_ID = 'DG2xFkPdDwKUoBkzGAhQtLpSGzfXLiCYPEzeKH2Ad24p'
WAVES_ASSET = pw.Asset(WAVES_ID)
USDN_ASSET = pw.Asset(USDN_ID)
ASSET_PAIR = pw.AssetPair(WAVES_ASSET, USDN_ASSET)
TIME_SLEEP = 10


def get_orderbook_binance():
    order_book = requests.get('https://api3.binance.com/api/v3/depth?symbol=WAVESUSDT&limit=50').json()
    return order_book


def get_orderbook_waves_exchange():
    order_book = ASSET_PAIR.orderbook()
    return order_book


def calc_waves_for_usdt_binance(usdt_amount):
    if usdt_amount != int(usdt_amount):
        usdt_amount = int(usdt_amount)
    order_book = get_orderbook_binance()['asks']
    usdt_sum = 0
    waves_sum = 0
    for order in order_book:
        order_price = float(order[0])
        order_waves_amount = float(order[1])
        order_usdt_amount = order_price * order_waves_amount
        usdt_sum_diff = min((usdt_amount - usdt_sum, order_usdt_amount))
        usdt_sum += usdt_sum_diff
        waves_sum += (usdt_sum_diff / order_price)

        if usdt_sum >= usdt_amount:
            break

    return waves_sum


def calc_waves_for_usdn_wex(usdn_amount):
    if usdn_amount != int(usdn_amount):
        usdn_amount = int(usdn_amount)
    order_book = get_orderbook_waves_exchange()['asks']
    usdn_sum = 0
    waves_sum = 0
    for order in order_book:
        order_waves_amount = order['amount'] / 10 ** ASSET_PAIR.asset1.decimals
        order_price = order['price'] / 10 ** (8 + ASSET_PAIR.asset2.decimals - ASSET_PAIR.asset1.decimals)
        order_usdt_amount = order_price * order_waves_amount
        usdt_sum_diff = min((usdn_amount - usdn_sum, order_usdt_amount))
        usdn_sum += usdt_sum_diff
        waves_sum += (usdt_sum_diff / order_price)

        if usdn_sum >= usdn_amount:
            break

    return waves_sum


def calc_usdt_for_waves_bin(waves_amount):
    if waves_amount == str(waves_amount):
        waves_amount = int(waves_amount)
    order_book = get_orderbook_binance()['bids']
    usdt_sum = 0
    waves_sum = 0
    for order in order_book:
        order_price = float(order[0])
        order_waves_amount = float(order[1])
        waves_sum_diff = min(waves_amount - waves_sum, order_waves_amount)
        waves_sum += waves_sum_diff
        usdt_sum += (waves_sum_diff * order_price)

        if waves_sum >= waves_amount:
            break

    return usdt_sum


def calc_usdn_for_waves_wex(waves_amount):
    order_book = get_orderbook_waves_exchange()
    if waves_amount == str(waves_amount):
        waves_amount = int(waves_amount)
    order_book = order_book['bids']
    usdn_sum = 0
    waves_sum = 0
    for order in order_book:
        order_waves_amount = order['amount'] / 10 ** ASSET_PAIR.asset1.decimals
        order_price = order['price'] / 10 ** (8 + ASSET_PAIR.asset2.decimals - ASSET_PAIR.asset1.decimals)
        waves_sum_diff = min(waves_amount - waves_sum, order_waves_amount)
        waves_sum += waves_sum_diff
        usdn_sum += (waves_sum_diff * order_price)

        if waves_sum >= waves_amount:
            break

    return usdn_sum


def write_log(line):
    with open('price_deflect.txt', 'a', encoding='utf8') as file:
        file.write(line + '\n')


def get_amounts(amount):
    waves_sum_bin = calc_waves_for_usdt_binance(amount)
    usdn_sum_wex = calc_usdn_for_waves_wex(waves_sum_bin)
    waves_sum_wex = calc_waves_for_usdn_wex(amount)
    usdt_sum_bin = calc_usdt_for_waves_bin(waves_sum_wex)
    usdt_sell_price = usdn_sum_wex / amount
    usdt_buy_price = amount / usdt_sum_bin

    return usdt_sell_price, usdt_buy_price


def print_prices(sell_price, buy_price):
    print(f'SELL_PRICE = {sell_price:.3f}' + '\n' + f'BUY_PRICE = {buy_price:.3f}')
    print('------------------')


def write_log_line(prices_and_time_dict):
    if len(prices_and_time_dict['sell_prices']) == 1:
        direction = 'BIN --> WEX'
        line = '{} - {}. Цена продажи = {}'.format(prices_and_time_dict['times_sell_price'][0], direction,
        prices_and_time_dict['sell_prices'][0])
        write_log(line)
    elif len(prices_and_time_dict['buy_prices']) == 1:
        direction = 'WEX --> BIN'
        line = '{} - {}. Цена покупки = {}'.format(prices_and_time_dict['times_buy_price'][0], direction,
        prices_and_time_dict['buy_prices'][0])
        write_log(line)
    elif len(prices_and_time_dict['sell_prices']) > 1:
        direction = 'BIN --> WEX'
        line = '[{} - {}] - {}. Цена продажи: max = {}, min = {}'.format(prices_and_time_dict['times_sell_price'][0],
        prices_and_time_dict['times_sell_price'][-1], direction, max(prices_and_time_dict['sell_prices']),
        min(prices_and_time_dict['sell_prices']))
        write_log(line)
    elif len(prices_and_time_dict['buy_prices']) > 1:
        direction = 'WEX --> BIN'
        line = '[{} - {}] - {}. Цена покупки: max = {}, min = {}'.format(prices_and_time_dict['times_buy_price'][0],
        prices_and_time_dict['times_buy_price'][-1], direction, max(prices_and_time_dict['buy_prices']),
        min(prices_and_time_dict['buy_prices']))
        write_log(line)


def main(amount):
    sell_and_buy_price_dict = {}
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    while True:
        usdt_sell_price, usdt_buy_price = get_amounts(amount)
        if usdt_sell_price > 1.01:
            if 'sell_prices' not in sell_and_buy_price_dict.keys():
                sell_and_buy_price_dict['times_sell_price'] = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                sell_and_buy_price_dict['sell_prices'] = [usdt_sell_price]
            else:
                sell_and_buy_price_dict['times_sell_price'].append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                sell_and_buy_price_dict['sell_prices'].append(usdt_sell_price)
            time.sleep(TIME_SLEEP)
            continue

        elif usdt_buy_price < 0.99:
            if 'buy_prices' not in sell_and_buy_price_dict.keys():
                sell_and_buy_price_dict['times_buy_price'] = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                sell_and_buy_price_dict['buy_prices'] = [usdt_buy_price]
            else:
                sell_and_buy_price_dict['times_buy_price'].append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                sell_and_buy_price_dict['buy_prices'].append(usdt_buy_price)
            time.sleep(TIME_SLEEP)
            continue

        else:
            if len(sell_and_buy_price_dict.values()) > 0:
                if 'sell_prices' in sell_and_buy_price_dict.keys():
                    write_log_line(sell_and_buy_price_dict)

                elif 'buy_prices' in sell_and_buy_price_dict.keys():
                    write_log_line(sell_and_buy_price_dict)

                sell_and_buy_price_dict = {}
                time.sleep(TIME_SLEEP)
                continue

            else:
                print_prices(usdt_sell_price, usdt_buy_price)
                time.sleep(TIME_SLEEP)


main(amount=20000)