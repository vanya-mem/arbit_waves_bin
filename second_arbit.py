import pywaves as pw
import requests
from datetime import datetime
import time


WAVES_ID = ''
USDN_ID = 'DG2xFkPdDwKUoBkzGAhQtLpSGzfXLiCYPEzeKH2Ad24p'
WAVES_ASSET = pw.Asset(WAVES_ID)
USDN_ASSET = pw.Asset(USDN_ID)
ASSET_PAIR = pw.AssetPair(WAVES_ASSET, USDN_ASSET)


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
    get_time = datetime.now()
    with open('price_deflect.txt', 'a', encoding='utf8') as file:
        file.write(f'{get_time.hour}:{get_time.minute}:{get_time.second} - {get_time.day}.{get_time.month}.{get_time.year}'
                   + f'Отклонение = {line}')


def main(usdt_amount):
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    while True:
        waves_sum = calc_waves_for_usdt_binance(usdt_amount)
        usdn_sum = calc_usdn_for_waves_wex(waves_sum)
        price_deflection = usdn_sum / usdt_amount
        if price_deflection > 1.1:
            print('Найдено отклонение в цене')
            write_log(str(price_deflection))
        else:
            print('Отклонения в цене пока не найдено')
        time.sleep(10)


main(usdt_amount=20000)






