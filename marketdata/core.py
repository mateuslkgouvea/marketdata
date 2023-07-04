from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, Form, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import MetaTrader5 as mt5
import pandas as pd

from .user_data import records
from .params import defaults, timeframes, flags, dates
from .security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    Token,
    User,
    oauth2_scheme,
)

if not mt5.initialize():
    mt5.shutdown()
    raise RuntimeError('MetaTrader failed to initialize')


app = FastAPI()


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(records, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


def _parser(symbol:str, args:dict | None = None) -> dict:
    # ensure list
    try:
        symbol = eval(symbol)
    except NameError:
        symbol = [symbol.upper()]

    date_fields =  ['date_from', 'date_to']

    if args is None:
        return symbol

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
async def index(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    return 'marketdata API'


@app.get('/mt5/', dependencies= [Depends(get_current_active_user)])
async def mt5_index():
    return mt5.version()


# Symbols
@app.get('/mt5/symbols/', dependencies= [Depends(get_current_active_user)])
async def get_symbols(group:str | None = None) -> list:
    if group is not None:
        ans = mt5.symbols_get(group.upper())
    else:
        ans = mt5.symbols_get()
    ans = [a._asdict() for a in ans]
    return ans


@app.get('/mt5/symbols/total/', dependencies= [Depends(get_current_active_user)])
async def get_symbols_total() -> int:
    return mt5.symbols_total()


@app.get('/mt5/symbol/info/{symbol}', dependencies= [Depends(get_current_active_user)])
async def get_symbol_info(symbol:str) -> dict[str, dict | None]:
    symbol = _parser(symbol)
    info = {}
    for s in symbol:
        temp = mt5.symbol_info(s)
        if temp is not None:
            temp = temp._asdict()
        info[s] = temp
    return info


@app.get('/mt5/symbol/info/tick/{symbol}', dependencies= [Depends(get_current_active_user)])
async def get_symbol_info_tick(symbol:str) -> dict[str, dict | None]:
    symbol = _parser(symbol)
    info = {}
    for s in symbol:
        temp = mt5.symbol_info_tick(s)
        if temp is not None:
            temp = temp._asdict()
        info[s] = temp
    return info


# Book
@app.get('/mt5/book/{symbol}', dependencies= [Depends(get_current_active_user)])
async def get_book(symbol: str) -> dict[str, str | None]:
    symbol = _parser(symbol)
    book = {}
    for s in symbol:
        mt5.market_book_add(s)
        temp = mt5.market_book_get(s)
        mt5.market_book_release(s)
        if temp is not None:
            temp = [b._asdict() for b in temp]
            temp = pd.DataFrame(temp).to_json()
        book[s] = temp
    return book


# Rates
@app.get('/mt5/rates/range/{symbol}', dependencies= [Depends(get_current_active_user)])
async def get_rates_range(
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


@app.get('/mt5/rates/from/{symbol}', dependencies= [Depends(get_current_active_user)])
async def get_rates_from(
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
    for s in symbol:
        temp = mt5.copy_rates_from(
            s,
            args['timeframe'],
            args['date_from'],
            args['count']
        )
        if temp is not None:
            temp = pd.DataFrame(temp).to_json()
        else:
            temp = None
        rates[s] = temp
    return rates


@app.get('/mt5/rates/from/pos/{symbol}', dependencies= [Depends(get_current_active_user)])
async def get_rates_from_pos(
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
    for s in symbol:
        temp = mt5.copy_rates_from_pos(
            s,
            args['timeframe'],
            args['start_pos'],
            args['count']
        )
        if temp is not None:
            temp = pd.DataFrame(temp).to_json()
        else:
            temp = None
        rates[s] = temp
    return rates


# Ticks
@app.get('/mt5/ticks/range/{symbol}', dependencies= [Depends(get_current_active_user)])
async def get_ticks_range(
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
    for s in symbol:
        temp = mt5.copy_ticks_range(
            s,
            args['date_from'],
            args['date_to'],
            args['flags']
        )
        if temp is not None:
            temp = pd.DataFrame(temp).to_json()
        else:
            temp = None
        rates[s] = temp
    return rates


@app.get('/mt5/ticks/from/{symbol}', dependencies= [Depends(get_current_active_user)])
async def get_ticks_from(
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
    for s in symbol:
        temp = mt5.copy_ticks_from(
            s,
            args['date_from'],
            args['count'],
            args['flags']
        )
        if temp is not None:
            temp = pd.DataFrame(temp).to_json()
        else:
            temp = None
        rates[s] = temp
    return rates