from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from datetime import datetime

import MetaTrader5 as mt5
import pandas as pd

from .params import defaults, timeframes, flags, dates

app = FastAPI()

if not mt5.initialize():
    mt5.shutdown()
    raise RuntimeError('MetaTrader failed to initialize')

def _parser(symbol, args:dict) -> dict:
    # ensure list
    try:
        symbol = eval(symbol)
    except NameError:
        symbol = [symbol]

    date_fields =  ['date_from', 'date_to']

    for param, value in args.items():
        # parse
        if param == 'timeframe' and value is not None:
            args[param] = timeframes[value]
        elif param == 'flags' and value is not None:
            args[param] = flags[value]
        elif param in date_fields and value is not None:
            if value in dates.keys():
                value = dates[value]
            else:
                value = datetime.strptime(value, '%Y-%m-%d')
            args[param] = value
        # fill
        if value is None:
            args[param] = getattr(defaults, param)
    
    return symbol, args

@app.get('/')
def index():
    return 'marketdata API'

@app.get('/symbols/')
def get_symbol(group:str | None = None) -> list:
    if group is not None:
        ans = mt5.symbols_get(group)
    else:
        ans = mt5.symbols_get()
    ans = [a._asdict() for a in ans]
    return ans

# Rates
@app.get('/rates/range/{symbol}')
def get_rates_range(
    symbol: str,
    timeframe: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None
) -> dict[str, str | None]:
    # parse parameters
    args = {'timeframe': timeframe, 
            'date_from': date_from,
            'date_to': date_to}
    symbol, args = _parser(symbol, args)
    # query
    rates = {}
    for symbol in symbol:
        temp = mt5.copy_rates_range(
            symbol,
            args['timeframe'],
            args['date_from'],
            args['date_to']
        )
        if temp is not None:
            temp = pd.DataFrame(temp).to_json()
        else:
            temp = None
        rates[symbol] = temp
    return rates

@app.get('/rates/from/{symbol}')
def get_rates_from(
    symbol: str,
    timeframe: str | None = None,
    date_from: str | None = None,
    count: int | None = None
) -> dict[str, str | None]:
    # parse parameters
    args = {'timeframe': timeframe, 
            'date_from': date_from,
            'count': count}
    symbol, args = _parser(symbol, args)
    # query
    rates = {}
    for symbol in symbol:
        temp = mt5.copy_rates_from(
            symbol,
            args['timeframe'],
            args['date_from'],
            args['count']
        )
        if temp is not None:
            temp = pd.DataFrame(temp).to_json()
        else:
            temp = None
        rates[symbol] = temp
    return rates

@app.get('/rates/from/pos/{symbol}')
def get_rates_from_pos(
    symbol: str,
    timeframe: str | None = None,
    start_pos: int | None = None,
    count: int | None = None
) -> dict[str, str | None]:
    # parse parameters
    args = {'timeframe': timeframe, 
            'start_pos': start_pos,
            'count': count}
    symbol, args = _parser(symbol, args)
    # query
    rates = {}
    for symbol in symbol:
        temp = mt5.copy_rates_from_pos(
            symbol,
            args['timeframe'],
            args['start_pos'],
            args['count']
        )
        if temp is not None:
            temp = pd.DataFrame(temp).to_json()
        else:
            temp = None
        rates[symbol] = temp
    return rates

# Ticks
@app.get('/ticks/range/{symbol}')
def get_ticks_range(
    symbol: str,
    date_from: str | None = None,
    date_to: str | None = None,
    flags: str | None = None,
) -> dict[str, str | None]:
    # parse parameters
    args = {'date_from': date_from,
            'date_to': date_to,
            'flags':flags}
    symbol, args = _parser(symbol, args)
    # query
    rates = {}
    for symbol in symbol:
        temp = mt5.copy_ticks_range(
            symbol,
            args['date_from'],
            args['date_to'],
            args['flags']
        )
        if temp is not None:
            temp = pd.DataFrame(temp).to_json()
        else:
            temp = None
        rates[symbol] = temp
    return rates

@app.get('/ticks/from/{symbol}')
def get_ticks_from(
    symbol: str,
    date_from: str | None = None,
    count: int | None = None,
    flags: str | None = None,
) -> dict[str, str | None]:
    # parse parameters
    args = {'date_from': date_from,
            'count': count,
            'flags':flags}
    symbol, args = _parser(symbol, args)
    # query
    rates = {}
    for symbol in symbol:
        temp = mt5.copy_ticks_from(
            symbol,
            args['date_from'],
            args['count'],
            args['flags']
        )
        if temp is not None:
            temp = pd.DataFrame(temp).to_json()
        else:
            temp = None
        rates[symbol] = temp
    return rates