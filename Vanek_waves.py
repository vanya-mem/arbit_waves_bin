import pywaves as pw
import requests
from datetime import datetime
import time

WAVES_ID = ''
USDN_ID = 'DG2xFkPdDwKUoBkzGAhQtLpSGzfXLiCYPEzeKH2Ad24p'
get_time = datetime.now()
hour, minutes, seconds, day, month, year = get_time.hour, get_time.minute, get_time.second, get_time.day, get_time.month,\
                                           get_time.year


def get_orderbook_wex():
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    waves_asset = pw.Asset(WAVES_ID)
    usdn_asset = pw.Asset(USDN_ID)
    asset_pair = pw.AssetPair(waves_asset, usdn_asset)
    order_book = asset_pair.orderbook()
    return order_book, asset_pair


def get_orderbook_bin():
    order_book = requests.get('https://api3.binance.com/api/v3/depth?symbol=WAVESUSDT&limit=50').json()
    return order_book


def get_orders_by_type(user_type, order_book):
    user_type = user_type.lower()
    if user_type == 'buy':
        return order_book['asks']
    elif user_type == 'sell':
        return order_book['bids']
    else:
        raise Exception('Type должен быть либо Sell, либо Buy')


def calc_waves_for_usdt_bin_wex(usdtAmount, Type):
    order_book, asset_pair = get_orderbook_wex()
    if usdtAmount == str(usdtAmount):
        usdtAmount = int(usdtAmount)
    order_book = get_orders_by_type(Type, order_book)
    usdt_sum = 0
    waves_sum = 0
    for order in order_book:
        order_waves_amount = order['amount'] / 10 ** asset_pair.asset1.decimals
        order_price = order['price'] / 10 ** (8 + asset_pair.asset2.decimals - asset_pair.asset1.decimals)
        order_usdt_amount = order_price * order_waves_amount
        usdt_sum_diff = min(usdtAmount - usdt_sum, order_usdt_amount)
        usdt_sum += usdt_sum_diff
        waves_sum += (usdt_sum_diff / order_price)

        if usdt_sum >= usdtAmount:
            break

    return waves_sum


def calc_waves_for_usdt_bin_bin(usdtAmount, Type):
    if usdtAmount == str(usdtAmount):
        usdtAmount = int(usdtAmount)
    order_book = get_orderbook_bin()
    order_book = get_orders_by_type(Type, order_book)
    usdt_sum = 0
    waves_sum = 0
    for order in order_book:
        order_price = float(order[0])
        order_waves_amount = float(order[1])
        order_usdt_amount = order_price * order_waves_amount
        usdt_sum_diff = min(usdtAmount - usdt_sum, order_usdt_amount)
        usdt_sum += usdt_sum_diff
        waves_sum += (usdt_sum_diff / order_price)

        if usdt_sum >= usdtAmount:
            break

    return waves_sum


def calc_usdt_for_waves_bin(wavesAmount, Type):
    if wavesAmount == str(wavesAmount):
        wavesAmount = int(wavesAmount)
    order_book = get_orderbook_bin()
    order_book = get_orders_by_type(Type, order_book)
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


def calc_usdt_for_waves_wex(wavesAmount, Type):
    order_book, asset_pair = get_orderbook_wex()
    if wavesAmount == str(wavesAmount):
        wavesAmount = int(wavesAmount)
    order_book = get_orders_by_type(Type, order_book)
    usdt_sum = 0
    waves_sum = 0
    for order in order_book:
        order_waves_amount = order['amount'] / 10 ** asset_pair.asset1.decimals
        order_price = order['price'] / 10 ** (8 + asset_pair.asset2.decimals - asset_pair.asset1.decimals)
        waves_sum_diff = min(wavesAmount - waves_sum, order_waves_amount)
        waves_sum += waves_sum_diff
        usdt_sum += (waves_sum_diff * order_price)

        if waves_sum >= wavesAmount:
            break

    return usdt_sum


def get_amount(user_type, usdtAmount):
    buy_waves_bin = 0
    sell_waves_wex = 0
    buy_waves_wex = 0
    sell_waves_bin = 0
    get_type = user_type.lower()
    if usdtAmount == int(usdtAmount):
        if get_type == 'buy':
            buy_waves_bin += calc_waves_for_usdt_bin_bin(usdtAmount, get_type)
            sell_waves_wex += calc_usdt_for_waves_wex(buy_waves_bin, 'sell')
            buy_waves_wex += calc_waves_for_usdt_bin_wex(usdtAmount, get_type)
            sell_waves_bin += calc_usdt_for_waves_bin(buy_waves_wex, 'sell')
        elif get_type == 'sell':
            buy_waves_bin = calc_waves_for_usdt_bin_bin(usdtAmount, get_type)
            sell_waves_wex = calc_usdt_for_waves_wex(buy_waves_bin, 'buy')
            buy_waves_wex = calc_waves_for_usdt_bin_wex(usdtAmount, get_type)
            sell_waves_bin = calc_usdt_for_waves_bin(buy_waves_wex, 'buy')

    return sell_waves_wex, sell_waves_bin, usdtAmount, user_type


def write_logs(arbit_percent, line):
    if arbit_percent > 3:
        with open('arbit_log.txt', 'a', encoding='utf8') as file:
            file.write(line)


def main(user_type, usdtAmount):
    while True:
        usdt_amount_wex, usdt_amount_bin, all_usdt_amount, get_user_type = get_amount(user_type, usdtAmount)
        get_type = user_type.lower()
        if get_type == 'buy':
            print(f'BIN --> WEX: {all_usdt_amount}$ --> {usdt_amount_wex}')
            print(f'WEX --> BIN: {all_usdt_amount}$ --> {usdt_amount_bin}')
        elif get_type == 'sell':
            print(f'BIN --> WEX: {all_usdt_amount}$ --> {usdt_amount_wex}')
            print(f'WEX --> BIN: {all_usdt_amount}$ --> {usdt_amount_bin}')
        min_usdt_amount = min(usdt_amount_bin, usdt_amount_wex)
        max_usdt_amount = max(usdt_amount_wex, usdt_amount_bin)
        arbit_percent = 100 - ((min_usdt_amount / max_usdt_amount) * 100)
        writing_log_line = f'{hour}:{minutes}:{seconds} - {day}.{month}.{year} - арбитраж равен {arbit_percent:.1f}' + '\n'
        write_logs(arbit_percent, line=writing_log_line)
        time.sleep(10)


main('sell', 20000)