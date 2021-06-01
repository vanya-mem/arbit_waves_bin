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
    get_time = datetime.now()
    hour = get_time.hour
    minute = get_time.minute
    seconds = get_time.second
    day = get_time.day
    month = get_time.month
    year = get_time.year
    with open('arbit_log.txt', 'a', encoding='utf8') as file:
        file.write(line + '\n')


def main(usdt_amount):
    arbit_percent_mass = []
    arbit_time_mass = []
    second_counter = 0
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    while True:
        time_start = time.time()
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
        if second_counter < 600:
            if arbit_percent > 1.5:
                arbit_percent_mass.append(arbit_percent)
                arbit_time_mass.append(datetime.now())
                second_counter = 0
                time.sleep(10)
                continue
        elif second_counter >= 600:
            if len(arbit_percent_mass) < 1:
                continue
            max_arbit_percent = max(arbit_percent_mass)
            min_arbit_percent = min(arbit_percent_mass)
            writing_log_line = '[{} - {}] - {}, min = {:.2f}, max = {:.2f}'.format(arbit_time_mass[0], arbit_time_mass[-1],
                    arbit_side, min_arbit_percent, max_arbit_percent)
            second_counter = 0
            write_logs(line=writing_log_line)
            arbit_time_mass.clear()
            arbit_percent_mass.clear()
            time.sleep(10)
            continue
        time_finish = time.time()
        if second_counter >= 600:
            if len(arbit_percent_mass) > 0:
                max_arbit_percent = max(arbit_percent_mass)
                min_arbit_percent = min(arbit_percent_mass)
                writing_log_line = '[{} - {}] - {}, min = {:.2f}, max = {:.2f}'.format(arbit_time_mass[0], arbit_time_mass[-1],
                        arbit_side, min_arbit_percent, max_arbit_percent)
                write_logs(writing_log_line)
                arbit_time_mass.clear()
                arbit_percent_mass.clear()
            second_counter = 0
        else:
            second_counter += time_finish - time_start + 10
        time.sleep(TIME_SLEEP)


main(20000)