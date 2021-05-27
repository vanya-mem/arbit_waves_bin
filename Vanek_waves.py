import pywaves as pw
import requests

WAVES_ID = ''
USDN_ID = 'DG2xFkPdDwKUoBkzGAhQtLpSGzfXLiCYPEzeKH2Ad24p'


def getting_waves_depth(usdtAmount, Type):
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    waves_asset = pw.Asset(WAVES_ID)
    usdn_asset = pw.Asset(USDN_ID)
    asset_pair = pw.AssetPair(waves_asset, usdn_asset)
    order_book = asset_pair.orderbook()

    if usdtAmount == str(usdtAmount):
        usdtAmount = int(usdtAmount)

    Type = Type.lower()
    if Type == 'buy':
        order_book = order_book['asks']
    elif Type == 'sell':
        order_book = order_book['bids']
    else:
        raise Exception('Type должен быть либо Sell, либо Buy')
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
    Type = Type.lower()
    if Type == 'buy':
        order_book = order_book['asks']
    elif Type == 'sell':
        order_book = order_book['bids']
    else:
        raise Exception('Type должен быть либо Sell, либо Buy')
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
    Type = Type.lower()
    if Type == 'buy':
        order_book = order_book['asks']
    elif Type == 'sell':
        order_book = order_book['bids']
    else:
        raise Exception('Type должен быть либо Sell, либо Buy')
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
    pw.setNode(node='http://nodes.wavesnodes.com', chain='mainnet')
    pw.setMatcher(node='https://matcher.waves.exchange')
    waves_asset = pw.Asset(WAVES_ID)
    usdn_asset = pw.Asset(USDN_ID)
    asset_pair = pw.AssetPair(waves_asset, usdn_asset)
    order_book = asset_pair.orderbook()

    if wavesAmount == str(wavesAmount):
        wavesAmount = int(wavesAmount)

    Type = Type.lower()
    if Type == 'buy':
        order_book = order_book['asks']
    elif Type == 'sell':
        order_book = order_book['bids']
    else:
        raise Exception('Type должен быть либо Sell, либо Buy')
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


print(getting_waves_depth(20000, 'buy'))
print(getting_binance_depth(usdtAmount=20000, Type='sell'))
print(calc_usdt_for_waves_bin(1219, 'sell'))
print(calc_usdt_for_waves_wex(1207, 'sell'))