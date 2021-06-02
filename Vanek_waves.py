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


def get_orderbook_wex():
    order_book = ASSET_PAIR.orderbook()
    return order_book


def get_orderbook_bin():
    order_book = requests.get('https://api3.binance.com/api/v3/depth?symbol=WAVESUSDT&limit=50').json()
    return order_book


def calc_waves_for_usdt_bin(usdt_amount):
    if usdt_amount != int(usdt_amount):
        usdt_amount = int(usdt_amount)
    order_book = get_orderbook_bin()['asks']
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


def calc_waves_for_usdt_wex(usdt_amount):
    if usdt_amount != int(usdt_amount):
        usdt_amount = int(usdt_amount)
    order_book = get_orderbook_wex()['asks']
    usdt_sum = 0
    waves_sum = 0
    for order in order_book:
        order_waves_amount = order['amount'] / 10 ** ASSET_PAIR.asset1.decimals
        order_price = order['price'] / 10 ** (8 + ASSET_PAIR.asset2.decimals - ASSET_PAIR.asset1.decimals)
        order_usdt_amount = order_price * order_waves_amount
        usdt_sum_diff = min((usdt_amount - usdt_sum, order_usdt_amount))
        usdt_sum += usdt_sum_diff
        waves_sum += (usdt_sum_diff / order_price)

        if usdt_sum >= usdt_amount:
            break

    return waves_sum


def calc_usdt_for_waves_bin(waves_amount):
    if waves_amount == str(waves_amount):
        waves_amount = int(waves_amount)
    order_book = get_orderbook_bin()['bids']
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


def calc_usdt_for_waves_wex(waves_amount):
    order_book = get_orderbook_wex()
    if waves_amount == str(waves_amount):
        waves_amount = int(waves_amount)
    order_book = order_book['bids']
    usdt_sum = 0
    waves_sum = 0
    for order in order_book:
        order_waves_amount = order['amount'] / 10 ** ASSET_PAIR.asset1.decimals
        order_price = order['price'] / 10 ** (8 + ASSET_PAIR.asset2.decimals - ASSET_PAIR.asset1.decimals)
        waves_sum_diff = min(waves_amount - waves_sum, order_waves_amount)
        waves_sum += waves_sum_diff
        usdt_sum += (waves_sum_diff * order_price)

        if waves_sum >= waves_amount:
            break

    return usdt_sum


def get_amounts(usdt_amount):
    buy_waves_bin = 0
    sell_waves_wex = 0
    buy_waves_wex = 0
    sell_waves_bin = 0
    if usdt_amount == int(usdt_amount):
        buy_waves_bin += calc_waves_for_usdt_bin(usdt_amount)
        sell_waves_wex += calc_usdt_for_waves_wex(buy_waves_bin)
        buy_waves_wex += calc_waves_for_usdt_wex(usdt_amount)
        sell_waves_bin += calc_usdt_for_waves_bin(buy_waves_wex)

    return sell_waves_wex, sell_waves_bin


def write_logs(line):
    with open('arbit_log.txt', 'a', encoding='utf8') as file:
        file.write(line + '\n')


def main(usdt_amount):
    arbit_percent_dict = {'WEX-BIN': [], 'BIN-WEX': []}
    arbit_time_array_bin_to_wex = []
    arbit_time_array_wex_to_bin = []
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    while True:
        usdt_wex, usdt_bin = get_amounts(usdt_amount)
        print(f'BIN --> WEX: {usdt_amount}$ --> {usdt_wex:.2f}$')
        print(f'WEX --> BIN: {usdt_amount}$ --> {usdt_bin:.2f}$')
        print('---------------------------------')
        max_usdt_amount = max(usdt_wex, usdt_bin)
        arbit_side = None
        if max_usdt_amount == usdt_wex:
            arbit_side = 'BIN --> WEX'
        elif max_usdt_amount == usdt_bin:
            arbit_side = 'WEX --> BIN'
        arbit_percent = 100 - ((usdt_amount / max_usdt_amount) * 100)
        if arbit_percent > 1.5:
            if arbit_side == 'BIN --> WEX':
                arbit_time_array_bin_to_wex.append(datetime.now())
                arbit_percent_dict['BIN-WEX'].append(arbit_percent)
                time.sleep(TIME_SLEEP)
                continue
            elif arbit_side == 'WEX --> BIN':
                arbit_time_array_wex_to_bin.append(datetime.now())
                arbit_percent_dict['WEX-BIN'].append(arbit_percent)
                time.sleep(TIME_SLEEP)
                continue
        else:
            if len(arbit_percent_dict) > 0:
                if len(arbit_percent_dict['BIN-WEX']) > 0:
                    if len(arbit_percent_dict['BIN-WEX']) == 1:
                        write_arbit_side = 'BIN --> WEX'
                        arbit_percent = arbit_percent_dict['BIN-WEX']
                        write_short_log_line = '{} - {}. Арбитраж = {}'.format(arbit_time_array_bin_to_wex[0],
                        write_arbit_side, arbit_percent)
                        write_logs(write_short_log_line)
                        arbit_time_array_bin_to_wex.clear()
                        arbit_percent_dict['BIN-WEX'].clear()
                        time.sleep(TIME_SLEEP)
                        continue
                    write_arbit_side = 'BIN --> WEX'
                    max_aribt_percent = max(arbit_percent_dict['BIN-WEX'])
                    min_arbit_percent = min(arbit_percent_dict['BIN-WEX'])
                    write_log_line = '[{} - {}] - {}. Max = {}, min = {}'.format(arbit_time_array_bin_to_wex[0],
                    arbit_time_array_bin_to_wex[-1], write_arbit_side, max_aribt_percent, min_arbit_percent)
                    write_logs(write_log_line)
                    arbit_percent_dict['BIN-WEX'].clear()
                    arbit_time_array_bin_to_wex.clear()
                    time.sleep(TIME_SLEEP)
                    continue
                elif len(arbit_percent_dict['WEX-BIN']) > 0:
                    if len(arbit_percent_dict['WEX-BIN']) == 1:
                        write_arbit_side = 'WEX --> BIN'
                        arbit_percent = arbit_percent_dict['WEX-BIN']
                        write_short_log_line = '{} - {}. Арбитраж = {}'.format(arbit_time_array_wex_to_bin[0],
                        write_arbit_side, arbit_percent)
                        write_logs(write_short_log_line)
                        arbit_time_array_wex_to_bin.clear()
                        arbit_percent_dict['WEX-BIN'].clear()
                        time.sleep(TIME_SLEEP)
                        continue
                    write_arbit_side = 'WEX --> BIN'
                    max_aribt_percent = max(arbit_percent_dict['WEX-BIN'])
                    min_arbit_percent = min(arbit_percent_dict['WEX-BIN'])
                    write_log_line = '[{} - {}] - {}. Max = {}, min = {}'.format(arbit_time_array_wex_to_bin[0],
                    arbit_time_array_wex_to_bin[-1], write_arbit_side, max_aribt_percent, min_arbit_percent)
                    write_logs(write_log_line)
                    arbit_percent_dict['WEX-BIN'].clear()
                    arbit_time_array_wex_to_bin.clear()
                    time.sleep(TIME_SLEEP)
                    continue
            time.sleep(TIME_SLEEP)


main(20000)