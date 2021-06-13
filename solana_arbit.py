import requests
from datetime import datetime
import time


TIME_SLEEP = 15
TRANCHE_SIZE = 20000
TARGET_ARBITRAGE = 1.5
arbit_percent_array = []
time_array = []
direction = None


def get_orderbook_binance():
    order_book = requests.get('https://api3.binance.com/api/v3/depth?symbol=SOLUSDT&limit=50').json()
    return order_book


def get_orderbook_bonfida():
    order_book = requests.get('https://serum-api.bonfida.com/orderbooks/SOLUSDT').json()
    return order_book


def calc_sol_for_usdt_bin(usdt_amount):
    try:
        order_book = get_orderbook_binance()['asks']
    except Exception:
        if len(arbit_percent_array) > 0:
            write_log_line(arbit_percent_array, time_array, direction)
        main()

    usdt_sum = 0
    sol_sum = 0
    for order in order_book:
        order_price = float(order[0])
        order_sol_amount = float(order[1])
        order_usdt_amount = order_price * order_sol_amount
        usdt_sum_diff = min((usdt_amount - usdt_sum, order_usdt_amount))
        usdt_sum += usdt_sum_diff
        sol_sum += (usdt_sum_diff / order_price)

        if usdt_sum >= usdt_amount:
            break

    return sol_sum


def calc_sol_for_usdt_bonfida(usdt_amount):
    try:
        order_book = get_orderbook_bonfida()['data']['asks']
    except Exception:
        if len(arbit_percent_array) > 0:
            write_log_line(arbit_percent_array, time_array, direction)
        main()

    usdt_sum = 0
    sol_sum = 0
    for order in order_book:
        order_price = float(order['price'])
        order_sol_amount = float(order['size'])
        order_usdt_amount = order_price * order_sol_amount
        usdt_sum_diff = min((usdt_amount - usdt_sum, order_usdt_amount))
        usdt_sum += usdt_sum_diff
        sol_sum += (usdt_sum_diff / order_price)

        if usdt_sum >= usdt_amount:
            break

    return sol_sum


def calc_usdt_for_sol_bin(sol_amount):
    try:
        order_book = get_orderbook_binance()['bids']
    except Exception:
        if len(arbit_percent_array) > 0:
            write_log_line(arbit_percent_array, time_array, direction)
        main()

    usdt_sum = 0
    sol_sum = 0
    for order in order_book:
        order_price = float(order[0])
        order_sol_amount = float(order[1])
        sol_sum_diff = min(sol_amount - sol_sum, order_sol_amount)
        sol_sum += sol_sum_diff
        usdt_sum += (sol_sum_diff * order_price)

        if sol_sum >= sol_amount:
            break

    return usdt_sum


def calc_usdt_for_sol_bonfida(sol_amount):
    try:
        order_book = get_orderbook_bonfida()['data']['bids']
    except Exception:
        if len(arbit_percent_array) > 0:
            write_log_line(arbit_percent_array, time_array, direction)
        main()

    usdt_sum = 0
    sol_sum = 0
    for order in order_book:
        order_price = float(order['price'])
        order_sol_amount = float(order['size'])
        sol_sum_diff = min(sol_amount - sol_sum, order_sol_amount)
        sol_sum += sol_sum_diff
        usdt_sum += (sol_sum_diff * order_price)

        if sol_sum >= sol_amount:
            break

    return usdt_sum


def get_amounts(usdt_amount):
    sol_amount_bin = calc_sol_for_usdt_bin(usdt_amount)
    usdt_amount_bonfida = calc_usdt_for_sol_bonfida(sol_amount_bin)

    sol_amount_bonfida = calc_sol_for_usdt_bonfida(usdt_amount)
    usdt_amount_bin = calc_usdt_for_sol_bin(sol_amount_bonfida)

    return usdt_amount_bonfida, usdt_amount_bin


def print_amounts(usdt_amount, usdt_amount_bonfida, usdt_amount_bin):
    print(f'BIN --> BON: {usdt_amount}$ --> {usdt_amount_bonfida:.2f}$')
    print(f'BON --> BIN: {usdt_amount}$ --> {usdt_amount_bin:.2f}$')
    print('---------------------------------')


def write_log(line):
    print(line + '\n')
    with open('solana_arbit_log.txt', 'a', encoding='utf8') as file:
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
        usdt_amount_bonfida, usdt_amount_bin = get_amounts(TRANCHE_SIZE)
        print_amounts(TRANCHE_SIZE, usdt_amount_bonfida, usdt_amount_bin)

        arbit_percent_bin = ((usdt_amount_bin - TRANCHE_SIZE) / TRANCHE_SIZE) * 100
        arbit_percent_bonfida = ((usdt_amount_bonfida - TRANCHE_SIZE) / TRANCHE_SIZE) * 100

        if arbit_percent_bin > TARGET_ARBITRAGE:
            if direction is None:
                direction = 'BON --> BIN'
            elif direction == 'BIN --> BON':
                write_log_line(arbit_percent_array, time_array, direction)
                arbit_percent_array.clear()
                time_array.clear()
                direction = 'BON --> BIN'

            arbit_percent_array.append(arbit_percent_bin)
            time_array.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        elif arbit_percent_bonfida > TARGET_ARBITRAGE:
            if direction is None:
                direction = 'BIN --> BON'
            elif direction == 'BON --> BIN':
                write_log_line(arbit_percent_array, time_array, direction)
                arbit_percent_array.clear()
                time_array.clear()
                direction = 'BIN --> BON'

            arbit_percent_array.append(arbit_percent_bonfida)
            time_array.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        else:
            if len(arbit_percent_array) > 0:
                write_log_line(arbit_percent_array, time_array, direction)
                arbit_percent_array.clear()
                time_array.clear()
                direction = None

        time.sleep(TIME_SLEEP)


main()