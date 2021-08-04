from pyserum.connection import conn
from pyserum.market import Market
import requests

CONNECT_STATUS = None
BUY_PRICE = None
SELL_PRICE = None
PUBLIC_KEY = None
WALLET_ADRESS = ''


def check_connection():
    global CONNECT_STATUS
    try_to_connect = requests.get("https://api.mainnet-beta.solana.com/")
    if try_to_connect.status_code != 200:
        CONNECT_STATUS = False
    elif try_to_connect.status_code == 200:
        CONNECT_STATUS = True


def get_orderbook():
    check_connection()
    if CONNECT_STATUS is True:
        connection = conn('https://api.mainnet-beta.solana.com/')
        orderbook = Market.load(connection, 'HWHvQhFmJB3NUcu1aihKmrKegfVxBEHzwVX6yZCKEsi1')
        return orderbook
    elif CONNECT_STATUS is False:
        raise Exception('Не удалось установить соединение с сайтом')


def count_buy_price():
    global BUY_PRICE

    try:
        order_book = get_orderbook()
    except Exception as Error:
        print(Error)
        order_book = None

    if order_book is not None:
        buy_prices_array = []
        order_book_bids = order_book.load_bids()
        for bid in order_book_bids:
            buy_prices_array.append(bid.info.price)
        if BUY_PRICE is not None:
            if BUY_PRICE == buy_prices_array[-1]:
                pass
            elif BUY_PRICE != buy_prices_array[-1]:
                BUY_PRICE = buy_prices_array[-1] + 0.001
        elif BUY_PRICE is None:
            BUY_PRICE = buy_prices_array[-1] + 0.001
        buy_prices_array.clear()
    elif order_book is None:
        count_buy_price()


def count_sell_price():
    global BUY_PRICE, SELL_PRICE

    global BUY_PRICE

    try:
        order_book = get_orderbook()
    except Exception as Error:
        print(Error)
        order_book = None

    if order_book is not None:
        sell_prices_array = []
        order_book_asks = order_book.load_asks()
        for ask in order_book_asks:
            sell_prices_array.append(ask.info.price)
        if SELL_PRICE is not None:
            if SELL_PRICE == sell_prices_array[1]:
                pass
            elif SELL_PRICE != sell_prices_array[1]:
                SELL_PRICE = SELL_PRICE - 0.001
        elif SELL_PRICE is None:
            if float(SELL_PRICE) < (float(BUY_PRICE) - 0.001):
                count_buy_price()
                sell_prices_array.clear()
            elif float(SELL_PRICE) > (float(BUY_PRICE) - 0.001):
                SELL_PRICE = sell_prices_array[1] - 0.001
            sell_prices_array.clear()
    elif order_book is None:
        count_sell_price()


def place_buy_order():
    count_buy_price()
    Market.place_order(payer=PUBLIC_KEY, owner=WALLET_ADRESS, order_type=0, side=0, limit_price=BUY_PRICE,
                       max_quantity=1.5)


def place_sell_order():
    count_sell_price()
    Market.place_order(payer=PUBLIC_KEY, owner=WALLET_ADRESS, order_type=0, side=1, limit_price=SELL_PRICE)