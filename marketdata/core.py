from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext

import MetaTrader5 as mt5
import pandas as pd

from .params import defaults, timeframes, flags, dates

if not mt5.initialize():
    mt5.shutdown()
    raise RuntimeError('MetaTrader failed to initialize')

SECRET_KEY = "163d19449c79ed753e8ae87b4f70f44ac4528e75413b0f77e23722966f3c1bc9"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

db = {
    "Mateus":{
        "username":"mateuslkgouvea",
        "full_name": "Mateus Klein",
        "email": "mateuslkgouvea@hotmail.com",
        "hashed_password":"$2b$12$.bPLv559nI4MWBKhefYjI.m.Ub0u1I5ppcLBqz0J0pmZRjb2epvZ6",
        "disabled": False
    }
}

app = FastAPI()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDb(User):
    hashed_password:str

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username:str):
    if username in db:
        user_data = db[username]
        return UserInDb(**user_data)

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data:dict, expires_delta : timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes = 15)
    
    to_encode.update({'exp':expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)
    return encoded_jwt

async def get_current_user(token:str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = 'Could not validate credentials',
        headers = {'WWW_Authenticate':'Bearer'}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        username : str = payload.get("sub")
        if username is None:
            raise credential_exception
        
        token_data = TokenData(username = username)
    except JWTError:
        raise credential_exception
    
    user = get_user(db, username = token_data.username)
    if user is None:
        raise credential_exception
    
    return user

async def get_current_active_user(current_user: UserInDb = Depends(get_current_user)):
    if current_user.disabled:
        return HTTPException(status_code=400, detail = 'Inective user')

    return current_user

@app.post("/token", response_model = Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "Invalid credentials")
    access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub":user.username}, expires_delta= access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("users/me/", response_model = User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
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
def index():
    return mt5.version()

# Symbols
@app.get('/symbols/')
async def get_symbols(group:str | None = None) -> list:
    if group is not None:
        ans = mt5.symbols_get(group.upper())
    else:
        ans = mt5.symbols_get()
    ans = [a._asdict() for a in ans]
    return ans

@app.get('/symbols/total/')
async def get_symbols() -> int:
    return mt5.symbols_total()

@app.get('/symbol/info/{symbol}')
async def get_symbol_info(symbol:str) -> dict[str, dict | None]:
    symbol = _parser(symbol)
    info = {}
    for s in symbol:
        temp = mt5.symbol_info(s)
        if temp is not None:
            temp = temp._asdict()
        info[s] = temp
    return info

@app.get('/symbol/info/tick/{symbol}')
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
@app.get('/book/{symbol}')
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
@app.get('/rates/range/{symbol}')
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

@app.get('/rates/from/{symbol}')
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

@app.get('/rates/from/pos/{symbol}')
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
@app.get('/ticks/range/{symbol}')
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

@app.get('/ticks/from/{symbol}')
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