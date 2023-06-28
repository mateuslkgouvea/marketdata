from fastapi import FastAPI
import MetaTrader5 as mt5
import time

app = FastAPI()

if not mt5.initialize():
    mt5.shutdown()
    raise RuntimeError('MetaTrader failed to initialize')

timeframes = dict(m1 = mt5.TIMEFRAME_M1,
                  m5 = mt5.TIMEFRAME_M5,
                  m15 = mt5.TIMEFRAME_M15,
                  m30 = mt5.TIMEFRAME_M30,
                  h1 = mt5.TIMEFRAME_H1,
                  h4 = mt5.TIMEFRAME_H4,
                  d1 = mt5.TIMEFRAME_D1,
                  w1 = mt5.TIMEFRAME_W1,
                  mn = mt5.TIMEFRAME_MN1)


@app.get('/tickers/{group}')
def query_symbols(group = 'GROUP') -> dict:
    ans = mt5.symbols_get(group)
    ans = {a.name: a._asdict() for a in ans}
    return ans

@app.get('/ohlc/single/{ticker}')
def get_ohlc(ticker):
    pass