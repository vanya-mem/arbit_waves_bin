import pywaves as pw
import requests
from datetime import datetime
import time


WAVES_ID = ''
USDN_ID = 'DG2xFkPdDwKUoBkzGAhQtLpSGzfXLiCYPEzeKH2Ad24p'
WAVES_ASSET = pw.Asset(WAVES_ID)
USDN_ASSET = pw.Asset(USDN_ID)
ASSET_PAIR = pw.AssetPair(WAVES_ASSET, USDN_ASSET)
TIME_SLEEP = 15


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


def print_prices(sell_price, buy_price):
    print(f'SELL_PRICE = {sell_price:.3f}' + '\n' + f'BUY_PRICE = {buy_price:.3f}')
    print('------------------')


def main(amount):
    sell_and_buy_price_dict = {}
    time_array_sell_price = []
    time_array_buy_price = []
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    while True:
        waves_sum_bin = calc_waves_for_usdt_binance(amount)
        usdn_sum_wex = calc_usdn_for_waves_wex(waves_sum_bin)
        waves_sum_wex = calc_waves_for_usdn_wex(amount)
        usdt_sum_bin = calc_usdt_for_waves_bin(waves_sum_wex)
        usdt_sell_price = usdn_sum_wex / amount
        usdt_buy_price = amount / usdt_sum_bin

        if usdt_sell_price > 1.01:
            price_deflect_bin = 'BIN --> WEX'
            time_array_sell_price.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if price_deflect_bin not in sell_and_buy_price_dict.keys():
                sell_and_buy_price_dict[price_deflect_bin] = [usdt_sell_price]
            else:
                sell_and_buy_price_dict[price_deflect_bin].append(usdt_sell_price)
            time.sleep(TIME_SLEEP)
            continue

        elif usdt_buy_price < 0.99:
            price_deflect_wex = 'WEX --> BIN'
            time_array_buy_price.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if price_deflect_wex not in sell_and_buy_price_dict.keys():
                sell_and_buy_price_dict[price_deflect_wex] = [usdt_buy_price]
            else:
                sell_and_buy_price_dict[price_deflect_wex].append(usdt_buy_price)
            time.sleep(TIME_SLEEP)
            continue

        else:
            if len(sell_and_buy_price_dict.values()) > 0:
                if len(sell_and_buy_price_dict['BIN --> WEX']) > 0:
                    log_line = '[{} -{}] - {}, max = {}, min = {}'.format(time_array_sell_price[0],
                    time_array_sell_price[-1], 'BIN --> WEX', max(sell_and_buy_price_dict['sell_price']),
                    min(sell_and_buy_price_dict['BIN --> WEX']))
                    write_log(log_line)
                    time_array_sell_price.clear()

                log_line = '[{} -{}] - {}, max = {}, min = {}'.format(time_array_buy_price[0],
                time_array_buy_price[-1], 'WEX --> BIN', max(sell_and_buy_price_dict['WEX --> BIN']),
                min(sell_and_buy_price_dict['WEX --> BIN']))
                write_log(log_line)
                time_array_buy_price.clear()
                sell_and_buy_price_dict = {}
                time.sleep(TIME_SLEEP)
                continue

            else:
                print_prices(usdt_sell_price, usdt_buy_price)
                time.sleep(TIME_SLEEP)


main(amount=20000)






