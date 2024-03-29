import pywaves as pw
import requests
from datetime import datetime
import time


WAVES_ID = ''
USDN_ID = 'DG2xFkPdDwKUoBkzGAhQtLpSGzfXLiCYPEzeKH2Ad24p'
WAVES_ASSET = pw.Asset(WAVES_ID)
USDN_ASSET = pw.Asset(USDN_ID)
ASSET_PAIR = pw.AssetPair(WAVES_ASSET, USDN_ASSET)
TRANCHE_SIZE = 20000
TIME_SLEEP = 10
prices_array = []
time_array = []
direction = None


def get_orderbook_binance():
    order_book = requests.get('https://api3.binance.com/api/v3/depth?symbol=WAVESUSDT&limit=50').json()
    return order_book


def get_orderbook_waves_exchange():
    order_book = ASSET_PAIR.orderbook()
    return order_book


def calc_waves_for_usdt_binance(usdt_amount):
    try:
        order_book = get_orderbook_binance()
    except Exception:
        if len(prices_array) > 0:
            write_log_line(time_array, prices_array, direction)
        main(amount=TRANCHE_SIZE)
    else:
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
    try:
        order_book = get_orderbook_waves_exchange()
    except Exception:
        if len(prices_array) > 0:
            write_log_line(time_array, prices_array, direction)
        main(amount=TRANCHE_SIZE)
    else:
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
    try:
        order_book = get_orderbook_binance()
    except Exception:
        if len(prices_array) > 0:
            write_log_line(time_array, prices_array, direction)
        main(amount=TRANCHE_SIZE)
    else:
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
    try:
        order_book = get_orderbook_waves_exchange()
    except Exception:
        if len(prices_array) > 0:
            write_log_line(time_array, prices_array, direction)
        main(amount=TRANCHE_SIZE)
    else:
        order_book = get_orderbook_waves_exchange()['bids']

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


def write_log_line(time_array, prices_array, direction):
    if len(prices_array) == 1:
        log_line = '{} - {} - {}'.format(time_array[0], direction, prices_array[0])
        write_log(log_line)
    elif len(prices_array) > 1:
        log_line = '[{} - {}] - {}. Max = {}, min = {}'.format(time_array[0], time_array[-1], direction,
        max(prices_array), min(prices_array))
        write_log(log_line)


def main(amount):
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    while True:
        global direction
        usdt_sell_price, usdt_buy_price = get_amounts(amount)

        if usdt_sell_price > 1.01:  #BIN --> WEX
            if direction is None:
                direction = 'UP'
            elif direction == 'DOWN':
                write_log_line(time_array, prices_array, direction)
                time_array.clear()
                prices_array.clear()
                direction = 'UP'

            time_array.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            prices_array.append(usdt_sell_price)

        elif usdt_buy_price < 0.99:  #WEX --> BIN
            if direction is None:
                direction = 'DOWN'
            elif direction == 'UP':
                write_log_line(time_array, prices_array, direction)
                time_array.clear()
                prices_array.clear()
                direction = 'DOWN'

            time_array.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            prices_array.append(usdt_buy_price)

        else:
            if len(prices_array) > 0:
                write_log_line(time_array, prices_array, direction)
                time_array.clear()
                prices_array.clear()

        print_prices(usdt_sell_price, usdt_buy_price)
        time.sleep(TIME_SLEEP)


main(amount=TRANCHE_SIZE)