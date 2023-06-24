#!/usr/bin/env python
# coding: utf-8


import pyupbit
from binance.spot import Spot
import time
import logging
from binance.spot import Spot as Client
from binance.lib.utils import config_logging
from collections import namedtuple
from forex_python.converter import CurrencyRates
import urllib3
import sys
import os

#logging.getLogger("urllib3").setLevel(logging.WARNING)

access = ""
secret = ""
upbit = pyupbit.Upbit(access, secret)


config_logging(logging, logging.DEBUG)

spot_client = Client(base_url="https://api.binance.com")

binance_tickers = spot_client.book_ticker()

upbit_tickers = pyupbit.get_tickers("KRW")

def check_binance_upbit_arbitrage() : 
    upbit_withdraw_status = upbit.get_deposit_withdraw_status()

    c = CurrencyRates()
    usdt_krw_rate = c.get_rate('USD', 'KRW')

    TickerComparison = namedtuple('TickerComparison', ['binance_symbol', 'binance_price', 'upbit_symbol', 'upbit_price', 'usdt_krw_price', 'premium'])
    ticker_comparisons = []

    upbit_orderbooks = pyupbit.get_orderbook(ticker=upbit_tickers)

    for binance_ticker in binance_tickers:
        binance_symbol = binance_ticker['symbol']
        if binance_symbol.endswith('USDT'):
            upbit_symbol = 'KRW-' + binance_symbol[:-4]
            if upbit_symbol in upbit_tickers:
                binance_price = float(binance_ticker['bidPrice'])
                upbit_orderbook = next((orderbook for orderbook in upbit_orderbooks if orderbook['market'] == upbit_symbol), None)
                if upbit_orderbook is not None and len(upbit_orderbook['orderbook_units']) > 0:
                    highest_bid_price = upbit_orderbook['orderbook_units'][0]['bid_price']
                    lowest_ask_price = upbit_orderbook['orderbook_units'][0]['ask_price']
                    upbit_price = float(highest_bid_price)
                    if binance_symbol[:-4].endswith('XRP') or binance_symbol[:-4].endswith('TRX') :
                        upbit_price = float(lowest_ask_price)
                    if upbit_price == 0 or binance_price == 0:
                        continue
                    usdt_krw_price = binance_price * usdt_krw_rate
                    premium = (upbit_price / usdt_krw_price - 1) * 100 
                    wallet_state = next((data['wallet_state'] for data in upbit_withdraw_status if data['currency'] == binance_symbol[:-4]), None)
                    if wallet_state == 'working':
                        comparison = TickerComparison(binance_symbol, binance_price, upbit_symbol, upbit_price, usdt_krw_price, premium)
                        ticker_comparisons.append(comparison)

    sorted_ticker_comparisons = sorted(ticker_comparisons, key=lambda x: x.premium, reverse=True)

    trx_premium = max(p.premium for p in ticker_comparisons if p.upbit_symbol == 'KRW-TRX')
    xrp_premium = max(p.premium for p in ticker_comparisons if p.upbit_symbol == 'KRW-XRP')
    
    
    os.system('cls')

    if trx_premium > xrp_premium :
        print("Transfer with XRP, premium : ", xrp_premium)
    else :
        print("Transfer with TRX, premium : ", trx_premium)
    print("\n")

    premium_flag = False
    for comparison in sorted_ticker_comparisons:
        if comparison.premium > max(trx_premium, xrp_premium):
            adjusted_premium = comparison.premium - max(trx_premium, xrp_premium);
            print(f"{comparison.binance_symbol} - Premium remained: {adjusted_premium}")
            if adjusted_premium > 3 : 
                premium_flag = True

    if not premium_flag:
        print("\n\nBinance - Upbit Arbitrage Not Possible")


for i in range(100):    
    check_binance_upbit_arbitrage()
    time.sleep(1)




