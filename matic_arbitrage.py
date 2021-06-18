import requests
from datetime import datetime
import time


TRANCHE_SIZE = 5000
TIME_SLEEP = 15
TARGET_ARBITRAGE = 1.5
arbitrage_percent_array = []
time_array = []
direction = None


def get_orderbook_binance():
    try:
        order_book = requests.get('https://api3.binance.com/api/v3/depth?symbol=MATICUSDT&limit=50').json()
    except Exception:
        get_orderbook_binance()
    else:
        return order_book


def get_orderbook_okex():
    try:
        order_book = requests.get('https://okex.com/api/spot/v3/instruments/matic-usdt/book?size=50').json()
    except Exception:
        get_orderbook_okex()
    else:
        return order_book


def calc_matic_for_usdt_bin(usdt_amount):
    order_book = get_orderbook_binance()['asks']
    usdt_sum = 0
    matic_sum = 0
    for order in order_book:
        order_price = float(order[0])
        order_matic_amount = float(order[1])
        order_usdt_amount = order_price * order_matic_amount
        usdt_sum_diff = min((usdt_amount - usdt_sum, order_usdt_amount))
        usdt_sum += usdt_sum_diff
        matic_sum += (usdt_sum_diff / order_price)

        if usdt_sum >= usdt_amount:
            break

    return matic_sum


def calc_matic_for_usdt_okex(usdt_amount):
    order_book = get_orderbook_okex()['asks']
    usdt_sum = 0
    matic_sum = 0
    for order in order_book:
        order_price = float(order[0])
        order_matic_amount = float(order[1])
        order_usdt_amount = order_price * order_matic_amount
        usdt_sum_diff = min((usdt_amount - usdt_sum, order_usdt_amount))
        usdt_sum += usdt_sum_diff
        matic_sum += (usdt_sum_diff / order_price)

        if usdt_sum >= usdt_amount:
            break

    return matic_sum


def calc_usdt_for_matic_bin(matic_amount):
    order_book = get_orderbook_binance()['bids']
    usdt_sum = 0
    matic_sum = 0
    for order in order_book:
        order_price = float(order[0])
        order_matic_amount = float(order[1])
        sol_sum_diff = min(matic_amount - matic_sum, order_matic_amount)
        matic_sum += sol_sum_diff
        usdt_sum += (sol_sum_diff * order_price)

        if matic_sum >= matic_amount:
            break

    return usdt_sum


def calc_usdt_for_matic_okex(matic_amount):
    order_book = get_orderbook_okex()['bids']
    usdt_sum = 0
    matic_sum = 0
    for order in order_book:
        order_price = float(order[0])
        order_matic_amount = float(order[1])
        sol_sum_diff = min(matic_amount - matic_sum, order_matic_amount)
        matic_sum += sol_sum_diff
        usdt_sum += (sol_sum_diff * order_price)

        if matic_sum >= matic_amount:
            break

    return usdt_sum


def get_amounts(usdt_amount):
    matic_amount_bin = calc_matic_for_usdt_bin(usdt_amount)
    usdt_amount_okex = calc_usdt_for_matic_okex(matic_amount_bin)

    matic_amount_okex = calc_matic_for_usdt_okex(usdt_amount)
    usdt_amount_bin = calc_usdt_for_matic_bin(matic_amount_okex)

    return usdt_amount_okex, usdt_amount_bin


def print_amounts(usdt_amount, usdt_amount_okex, usdt_amount_bin):
    print(f'BIN --> OKEX: {usdt_amount}$ --> {usdt_amount_okex:.2f}$')
    print(f'OKEX --> BIN: {usdt_amount}$ --> {usdt_amount_bin:.2f}$')
    print('---------------------------------')


def write_log(line):
    print(line + '\n')
    with open('matic_log.txt', 'a', encoding='utf8') as file:
        file.write(line + '\n')


def write_log_line(arbit_percent_array, time_array, direction):
    if len(arbit_percent_array) == 1:
        log_line = '{} - {}. Арбитраж = {:.2f}%'.format(time_array[0], direction, arbit_percent_array[0])
        write_log(log_line)
    elif len(arbit_percent_array) > 1:
        log_line = '[{} - {}] - {}. Max = {:.2f}, min = {:.2f}'.format(time_array[0], time_array[-1], direction,
        max(arbit_percent_array), min(arbit_percent_array))
        write_log(log_line)


def main():
    while True:
        global direction
        usdt_amount_okex, usdt_amount_bin = get_amounts(TRANCHE_SIZE)
        print_amounts(TRANCHE_SIZE, usdt_amount_okex, usdt_amount_bin)

        arbit_percent_bin = ((usdt_amount_bin - TRANCHE_SIZE) / TRANCHE_SIZE) * 100
        arbit_percent_bonfida = ((usdt_amount_okex - TRANCHE_SIZE) / TRANCHE_SIZE) * 100

        if arbit_percent_bin > TARGET_ARBITRAGE:
            if direction is None:
                direction = 'OKEX --> BIN'
            elif direction == 'BIN --> OKEX':
                write_log_line(arbitrage_percent_array, time_array, direction)
                arbitrage_percent_array.clear()
                time_array.clear()
                direction = 'OKEX --> BIN'

            arbitrage_percent_array.append(arbit_percent_bin)
            time_array.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        elif arbit_percent_bonfida > TARGET_ARBITRAGE:
            if direction is None:
                direction = 'BIN --> OKEX'
            elif direction == 'OKEX --> BIN':
                write_log_line(arbitrage_percent_array, time_array, direction)
                arbitrage_percent_array.clear()
                time_array.clear()
                direction = 'BIN --> OKEX'

            arbitrage_percent_array.append(arbit_percent_bonfida)
            time_array.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        else:
            if len(arbitrage_percent_array) > 0:
                write_log_line(arbitrage_percent_array, time_array, direction)
                arbitrage_percent_array.clear()
                time_array.clear()
                direction = None

        time.sleep(TIME_SLEEP)


main()