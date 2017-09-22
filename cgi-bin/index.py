#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
from bittrex import Bittrex
from parser_coinmarketcap import get_last_price_usd, get_last_price_btc, get_last_ticker

# [0] - 'bitcoin'
# [1] - 'BTC'
# [2] - 0.08 // tokens
def read_extern_balances(filename):
    extern_balances = []
    for line in open(filename):
        if (line == '\n'):
            continue
        line = line.split('\n')
        line = line[0]
        line = line.split(' ')
        extern_balances.append(line)
    return extern_balances

# [0] - 'BTC'
# [1] - 1.0 // price in BTC
# [2] - 5000 // price in USD
def get_extern_rates(extern_balances):
    extern_rates = {}
    for item in extern_balances:
        try:
            ticker = get_last_ticker(item[0])
        except Exception, e:
            print(e)
            extern_rates[item[1]] = [0, 0]
            continue
        last_price_btc = float(ticker['price_btc'])
        last_price_usd = float(ticker['price_usd'])
        newrate = [last_price_btc, last_price_usd]
        extern_rates[item[1]] = newrate
    return extern_rates

# [0] - 'BTC'
# [1] - 0.08 // tokens
def get_bittrex_balances(bittrex):
    bittrex_balances = []
    actual = bittrex.get_balances()
    if is_success(actual):
        balances = actual['result']
        for item in balances:
            if (item['Balance'] > 0):
                currency = item['Currency']
                balance = item['Balance']
                bittrex_balances.append([currency, float(balance)])
    return bittrex_balances

# [0] - 'BTC'
# [1] - 1.0 // price in BTC
def get_bittrex_rates(balances):
    rates = {}
    for item in balances:
        xerate = 0.0
        market = 'none'
        currency = item[0]
        balance = item[1]
        if currency == 'BTC':
            xerate = 1.0
        elif currency == 'USDT':
            market = 'USDT-BTC'
        else:
            market = 'BTC-%s' % currency
        ticker = bittrex.get_ticker(market)
        if is_success(ticker):
            xerate = ticker['result']['Last']
            if currency == 'USDT':
                xerate = 1.0 / xerate
        rates[currency] = float(xerate)
    return rates

def is_success(response):
    return response['success'] == True


def main():
    global bittrex
    print("Content-type: text/html")
    print("")
    print("<h1>Beast fund</h1>")
    output = "<html><body><table>"
    #try:
    #    extern_balances = read_extern_balances('cgi-enabled/extern_balances.txt')
    #except:
    #    output += "Error reading external balances. Try again later."
    #    print(output)
    extern_balances = read_extern_balances('extern_balances.txt')
    extern_rates = {}
    try:
        extern_rates = get_extern_rates(extern_balances)
    except:
        output += "Coinmarketcap seems to be down. Response failed. Try again later."
        print(output)
    try:
        with open("bittrex_secrets.json") as secrets_file:
            secrets = json.load(secrets_file)
            secrets_file.close()
        bittrex = Bittrex(secrets['key'], secrets['secret'])
    except:
        output += "Internal problem reading secrets. Response failed. Try again later."
        print(output)
        return 1
    bittrex_balances = {}
    bittrex_rates = {}
    try:
        bittrex_balances = get_bittrex_balances(bittrex)
        bittrex_rates = get_bittrex_rates(bittrex_balances)
        total_balance_in_btc = 0.0
        for item in bittrex_balances:
            total_balance_in_btc += item[1] * bittrex_rates[item[0]]
        for item in extern_balances:
            total_balance_in_btc += float(item[2]) * extern_rates[item[1]][0]
    except:
        output += "Bittrex seems to be down. Response failed. Try again later."
        print(output)
        return 1
    output += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % \
              ("", "Units", "Last price", "Est. BTC value", "% (BTC)")
    for item in bittrex_balances:
        balance_in_btc = item[1] * bittrex_rates[item[0]]
        output += "<tr><td>%s</td><td>%.8f</td><td>%.8f</td><td>%.8f</td><td>%.2f%%</td></tr>" % \
                  (
                  item[0], item[1], bittrex_rates[item[0]], balance_in_btc, balance_in_btc / total_balance_in_btc * 100)
    for item in extern_balances:
        balance_in_btc = float(item[2]) * extern_rates[item[1]][0]
        output += "<tr><td>ext%s</td><td>%.8f</td><td>%.8f</td><td>%.8f</td><td>%.2f%%</td></tr>" % \
                  (item[1], float(item[2]), extern_rates[item[1]][0], balance_in_btc,
                   balance_in_btc / total_balance_in_btc * 100)
    output += "<tr><td>Total in BTC</td><td></td><td></td><td>%.8f</td></tr>" % total_balance_in_btc
    total_balance_in_usd = total_balance_in_btc * float(get_last_price_usd('bitcoin'))
    output += "<tr><td>Total in USD</td><td></td><td></td><td>%.8f</td></tr>" % total_balance_in_usd
    print(output)
    return 0

main()
