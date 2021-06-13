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
TRANCHE_SIZE = 20000
TARGET_ARBITRAGE = 1.5  # in percents
percents = []
timestamps = []
direction = None


def get_orderbook_wex():
    order_book = ASSET_PAIR.orderbook()
    return order_book


def get_orderbook_bin():
    order_book = requests.get('https://api3.binance.com/api/v3/depth?symbol=WAVESUSDT&limit=50').json()
    return order_book


def calc_waves_for_usdt_bin(usdt_amount):
    try:
        order_book = get_orderbook_bin()
    except Exception:
        if len(percents) > 0:
            log_arbitrage(percents, timestamps, direction)
        main()
    else:
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
    try:
        order_book = get_orderbook_wex()
    except Exception:
        if len(percents) > 0:
            log_arbitrage(percents, timestamps, direction)
        main()
    else:
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
    try:
        order_book = get_orderbook_bin()
    except Exception:
        if len(percents) > 0:
            log_arbitrage(percents, timestamps, direction)
        main()
    else:
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
    try:
        order_book = get_orderbook_wex()
    except Exception:
        if len(percents) > 0:
            log_arbitrage(percents, timestamps, direction)
        main()
    else:
        order_book = get_orderbook_wex()['bids']

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
    waves_amount = calc_waves_for_usdt_bin(usdt_amount)
    usdt_amount_wex = calc_usdt_for_waves_wex(waves_amount)

    waves_amount = calc_waves_for_usdt_wex(usdt_amount)
    usdt_amount_bin = calc_usdt_for_waves_bin(waves_amount)

    return usdt_amount_wex, usdt_amount_bin


def log(line):
    print(line + '\n')
    with open('arbit_log.txt', 'a', encoding='utf8') as file:
        file.write(line + '\n')


def log_arbitrage(percents, timestamps, direction):
    max_aribt_percent = max(percents)
    min_arbit_percent = min(percents)
    log(f'[{timestamps[0]} - {timestamps[-1]}] '
        f'{direction} max = {max_aribt_percent}, min = {min_arbit_percent}')


def print_amounts(usdt_amount, usdt_amount_wex, usdt_amount_bin):
    print(f'BIN --> WEX: {usdt_amount}$ --> {usdt_amount_wex:.2f}$')
    print(f'WEX --> BIN: {usdt_amount}$ --> {usdt_amount_bin:.2f}$')
    print('---------------------------------')


def main():
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    while True:
        global direction
        usdt_amount_wex, usdt_amount_bin = get_amounts(TRANCHE_SIZE)
        print_amounts(TRANCHE_SIZE, usdt_amount_wex, usdt_amount_bin)

        arbit_percent_wex = ((usdt_amount_wex - TRANCHE_SIZE) / TRANCHE_SIZE) * 100
        arbit_percent_bin = ((usdt_amount_bin - TRANCHE_SIZE) / TRANCHE_SIZE) * 100

        if arbit_percent_wex >= TARGET_ARBITRAGE:  # BIN --> WEX
            if direction is None:
                direction = 'BIN --> WEX'
            elif direction == 'WEX --> BIN':
                log_arbitrage(percents, timestamps, direction)
                percents.clear()
                timestamps.clear()
                direction = 'BIN --> WEX'

            timestamps.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            percents.append(arbit_percent_wex)
        elif arbit_percent_bin >= TARGET_ARBITRAGE:  # WEX --> BIN
            if direction is None:
                direction = 'WEX --> BIN'
            elif direction == 'BIN --> WEX':
                log_arbitrage(percents, timestamps, direction)
                percents.clear()
                timestamps.clear()
                direction = 'WEX --> BIN'

            timestamps.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            percents.append(arbit_percent_bin)
        elif direction is not None:
            log_arbitrage(percents, timestamps, direction)
            percents.clear()
            timestamps.clear()
            direction = None

        time.sleep(TIME_SLEEP)


main()