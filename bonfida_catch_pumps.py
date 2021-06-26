import requests
import time
from datetime import datetime

TIME_SLEEP = 10
TRANCHE_SIZE = 20000
timestamps = []
SOLANA_AMOUNT = 0
USDT_RESIDUE = 0


def get_orderbook_bonfida():
    try:
        order_book = requests.get('https://serum-api.bonfida.com/orderbooks/SOLUSDT').json()
    except Exception:
        get_orderbook_bonfida()
    else:
        return order_book


def calc_sol_for_usdt(usdt_amount):
    global USDT_RESIDUE, SOLANA_AMOUNT
    first_order_price = None
    first_order_amount = None
    count = 0
    order_book = get_orderbook_bonfida()
    for order in order_book['data']['bids']:
        if count < 1:
            first_order_price = float(order['price'])
            first_order_amount = float(order['size'])
            count += 1
            continue
        order_price = float(order['price'])
        if (100 - (first_order_price / order_price) * 100) >= 3:
            if first_order_amount >= 100:
                timestamps.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                if (first_order_price * first_order_amount) > TRANCHE_SIZE:
                    SOLANA_AMOUNT = usdt_amount / first_order_price
                    return SOLANA_AMOUNT
                SOLANA_AMOUNT = first_order_amount
                USDT_RESIDUE = usdt_amount - (first_order_price * SOLANA_AMOUNT)
                return SOLANA_AMOUNT

    return None


def calc_usdt_for_sol(sol_amount):
    first_order_price = None
    first_order_amount = None
    count = 0
    order_book = get_orderbook_bonfida()
    for order in order_book['data']['asks']:
        if count < 1:
            first_order_price = float(order['price'])
            first_order_amount = float(order['size'])
            count += 1
            continue
        order_price = float(order['price'])
        if (100 - (order_price / first_order_price) * 100) >= 3:
            if first_order_amount >= sol_amount:
                timestamps.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                usdt_amount = first_order_price * sol_amount
                return usdt_amount
    return None


def get_amounts():
    sol_amount = calc_sol_for_usdt(TRANCHE_SIZE)
    if sol_amount is not None:
        usdt_amount = calc_usdt_for_sol(sol_amount)
        if usdt_amount is not None:
            return usdt_amount

    return None


def write_logs(log_line):
    with open('bonfida_pumps.txt', 'a', encoding='utf8') as file:
        file.write(log_line + '\n')


def write_log_line(time_array, new_usdt_amount, usdt_amount):
    global USDT_RESIDUE, SOLANA_AMOUNT
    log_line = (f'Время покупки - {time_array[0]}, время продажи - {time_array[-1]}. Купили соланы на ' +
    f'{usdt_amount - USDT_RESIDUE}, получили - {new_usdt_amount - usdt_amount}.')
    write_logs(log_line)
    timestamps.clear()
    USDT_RESIDUE = 0
    SOLANA_AMOUNT = 0


def main():
    while True:
        new_usdt_amount = get_amounts()
        if new_usdt_amount is None:
            print('Пока ничего нет')
        elif new_usdt_amount is not None:
            print('Поймали скачок')
            write_log_line(timestamps, new_usdt_amount, TRANCHE_SIZE)
        time.sleep(TIME_SLEEP)


main()