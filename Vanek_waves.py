import pywaves as pw
import requests
from datetime import datetime
import time

WAVES_ID = ''
USDN_ID = 'DG2xFkPdDwKUoBkzGAhQtLpSGzfXLiCYPEzeKH2Ad24p'
WAVES_ASSET = pw.Asset(WAVES_ID)
USDN_ASSET = pw.Asset(USDN_ID)
ASSET_PAIR = pw.AssetPair(WAVES_ASSET, USDN_ASSET)


def get_orderbook_wex():
    order_book = ASSET_PAIR.orderbook()
    return order_book


def get_orderbook_bin():
    order_book = requests.get('https://api3.binance.com/api/v3/depth?symbol=WAVESUSDT&limit=50').json()
    return order_book


def calc_waves_sum(order_price, order_waves_amount, usdt_amount, waves_sum, usdt_sum):
    order_usdt_amount = order_price * order_waves_amount
    usdt_sum_diff = min(usdt_amount - usdt_sum, order_usdt_amount)
    usdt_sum += usdt_sum_diff
    waves_sum += (usdt_sum_diff / order_price)
    return usdt_sum_diff


def calc_waves_for_usdt(usdt_amount, orderbook):
    if usdt_amount != int(usdt_amount):
        usdt_amount = int(usdt_amount)
    order_book = orderbook['asks']
    usdt_sum = 0
    waves_sum = 0
    for order in order_book:
        try:
            if int(order['amount']) > 10 ** 8:
                order_waves_amount = order['amount'] / 10 ** ASSET_PAIR.asset1.decimals
                order_price = order['price'] / 10 ** (8 + ASSET_PAIR.asset2.decimals - ASSET_PAIR.asset1.decimals)
                usdt_sum_diff = calc_waves_sum(order_price, order_waves_amount, usdt_amount, waves_sum, usdt_sum)
                usdt_sum += usdt_sum_diff
                waves_sum += (usdt_sum_diff / order_price)
                if usdt_sum >= usdt_amount:
                    break
        except TypeError:
            order_price = float(order[0])
            order_waves_amount = float(order[1])
            usdt_sum_diff = calc_waves_sum(order_price, order_waves_amount, usdt_amount, waves_sum, usdt_sum)
            usdt_sum += usdt_sum_diff
            waves_sum += (usdt_sum_diff / order_price)
            if usdt_sum >= usdt_amount:
                break

    return waves_sum


def calc_usdt_for_waves_bin(wavesAmount):
    if wavesAmount == str(wavesAmount):
        wavesAmount = int(wavesAmount)
    order_book = get_orderbook_bin()['bids']
    usdt_sum = 0
    waves_sum = 0
    for order in order_book:
        order_price = float(order[0])
        order_waves_amount = float(order[1])
        waves_sum_diff = min(wavesAmount - waves_sum, order_waves_amount)
        waves_sum += waves_sum_diff
        usdt_sum += (waves_sum_diff * order_price)

        if waves_sum >= wavesAmount:
            break

    return usdt_sum


def calc_usdt_for_waves_wex(wavesAmount):
    order_book = get_orderbook_wex()
    if wavesAmount == str(wavesAmount):
        wavesAmount = int(wavesAmount)
    order_book = order_book['bids']
    usdt_sum = 0
    waves_sum = 0
    for order in order_book:
        order_waves_amount = order['amount'] / 10 ** ASSET_PAIR.asset1.decimals
        order_price = order['price'] / 10 ** (8 + ASSET_PAIR.asset2.decimals - ASSET_PAIR.asset1.decimals)
        waves_sum_diff = min(wavesAmount - waves_sum, order_waves_amount)
        waves_sum += waves_sum_diff
        usdt_sum += (waves_sum_diff * order_price)

        if waves_sum >= wavesAmount:
            break

    return usdt_sum


def get_amounts(usdtAmount):
    buy_waves_bin = 0
    sell_waves_wex = 0
    buy_waves_wex = 0
    sell_waves_bin = 0
    if usdtAmount == int(usdtAmount):
        buy_waves_bin += calc_waves_for_usdt(usdtAmount, orderbook=get_orderbook_bin())
        sell_waves_wex += calc_usdt_for_waves_wex(buy_waves_bin)
        buy_waves_wex += calc_waves_for_usdt(usdtAmount, orderbook=get_orderbook_wex())
        sell_waves_bin += calc_usdt_for_waves_bin(buy_waves_wex)

    return sell_waves_wex, sell_waves_bin, usdtAmount


def write_logs(line, arbit_percent):
    if arbit_percent > 3:
        get_time = datetime.now()
        hour = get_time.hour
        minute = get_time.minute
        seconds = get_time.second
        day = get_time.day
        month = get_time.month
        year = get_time.year
        with open('arbit_log.txt', 'a', encoding='utf8') as file:
            file.write(f'{hour}:{minute}:{seconds} - {day}.{month}.{year} - ' + line + '\n')


def main(usdtAmount):
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    while True:
        usdt_amount_wex, usdt_amount_bin, all_usdt_amount = get_amounts(usdtAmount)
        print(f'BIN --> WEX: {all_usdt_amount}$ --> {usdt_amount_wex:.2f}$')
        print(f'WEX --> BIN: {all_usdt_amount}$ --> {usdt_amount_bin:.2f}$')
        print('---------------------------------')
        max_usdt_amount = max(usdt_amount_wex, usdt_amount_bin)
        arbit_percent = 100 - ((all_usdt_amount / max_usdt_amount) * 100)
        writing_log_line = f'Арбитраж = {arbit_percent}%'
        write_logs(line=writing_log_line, arbit_percent=arbit_percent)
        time.sleep(10)


main(20000)