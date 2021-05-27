import pywaves as pw
import requests
from datetime import datetime

WAVES_ID = ''
USDN_ID = 'DG2xFkPdDwKUoBkzGAhQtLpSGzfXLiCYPEzeKH2Ad24p'
time = datetime.now()
hour, minutes, seconds, day, month, year = time.hour, time.minute, time.second, time.day, time.month, time.year


def connect_to_net_and_getting_orderbook_wex():
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    waves_asset = pw.Asset(WAVES_ID)
    usdn_asset = pw.Asset(USDN_ID)
    asset_pair = pw.AssetPair(waves_asset, usdn_asset)
    order_book = asset_pair.orderbook()
    return order_book, asset_pair


def getting_user_type(user_type, order_book):
    user_type = user_type.lower()
    if user_type == 'buy':
        return order_book['asks']
    elif user_type == 'sell':
        return order_book['bids']
    else:
        raise Exception('Type должен быть либо Sell, либо Buy')


def getting_waves_depth(usdtAmount, Type):
    order_book, asset_pair = connect_to_net_and_getting_orderbook_wex()
    if usdtAmount == str(usdtAmount):
        usdtAmount = int(usdtAmount)
    order_book = getting_user_type(Type, order_book)
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


def getting_binance_depth(usdtAmount, Type):
    if usdtAmount == str(usdtAmount):
        usdtAmount = int(usdtAmount)
    order_book = requests.get('https://api3.binance.com/api/v3/depth?symbol=WAVESUSDT&limit=50').json()
    order_book = getting_user_type(Type, order_book)
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
    order_book = requests.get('https://api3.binance.com/api/v3/depth?symbol=WAVESUSDT&limit=50').json()
    order_book = getting_user_type(Type, order_book)
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
    order_book, asset_pair = connect_to_net_and_getting_orderbook_wex()
    if wavesAmount == str(wavesAmount):
        wavesAmount = int(wavesAmount)
    order_book = getting_user_type(Type, order_book)
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


def main(user_type, usdtAmount):
    buy_waves_bin = 0
    sell_waves_wex = 0
    buy_waves_wex = 0
    sell_waves_bin = 0
    if usdtAmount == int(usdtAmount):
        Type = user_type.lower()
        if Type == 'buy':
            buy_waves_bin += getting_binance_depth(usdtAmount, Type)
            print(f'Купили {buy_waves_bin} waves на binance')
            sell_waves_wex += calc_usdt_for_waves_wex(buy_waves_bin, 'sell')
            print(f'Получили {sell_waves_wex}$, продав на waves exchange')
            buy_waves_wex += getting_waves_depth(usdtAmount, Type)
            print(f'Купили {buy_waves_wex} waves на waves exchange')
            sell_waves_bin += calc_usdt_for_waves_bin(buy_waves_wex, 'sell')
            print(f'Получили {sell_waves_bin}$, продав binance')
        elif Type == 'sell':
            buy_waves_bin = getting_binance_depth(usdtAmount, Type)
            print(f'Купили {buy_waves_bin} waves на binance')
            sell_waves_wex = calc_usdt_for_waves_wex(buy_waves_bin, 'buy')
            print(f'Получили {sell_waves_wex}$, продав на waves exchange')
            buy_waves_wex = getting_waves_depth(usdtAmount, Type)
            print(f'Купили {buy_waves_wex} waves на waves exchange')
            sell_waves_bin = calc_usdt_for_waves_bin(buy_waves_wex, 'buy')
            print(f'Получили {sell_waves_bin}$, продав binance')

    return sell_waves_wex, sell_waves_bin, usdtAmount, user_type


def writing_logs(arbit_percent, line):
    if arbit_percent >= 1:
        with open('arbit_log.txt', 'a', encoding='utf8') as file:
            file.write(line)


def get_arbit():
    usdt_amount_wex, usdt_amount_bin, all_usdt_amount, user_type = main('sell', 50000)
    min_usdt_amount = min(usdt_amount_bin, usdt_amount_wex)
    max_usdt_amount = max(usdt_amount_wex, usdt_amount_bin)
    arbit_percent = 100 - ((min_usdt_amount / max_usdt_amount) * 100)
    writing_log_line = f'{hour}:{minutes}:{seconds} - {day}.{month}.{year} - арбитраж равен {arbit_percent:.1f}' + '\n'
    writing_logs(arbit_percent, line=writing_log_line)


get_arbit()