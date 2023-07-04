from types import SimpleNamespace
from datetime import datetime

from dateutil.relativedelta import relativedelta
from pytz import timezone
import MetaTrader5 as mt5


TODAY = datetime.today()\
    .replace(hour = 0, minute = 0, second = 0, microsecond = 0, tzinfo = timezone("Etc/UTC"))

dates = dict(
    TODAY = TODAY,
    TRAILING_12M = TODAY + relativedelta(years = -1),
    TRAILING_6M = TODAY + relativedelta(months = -6),
    TRAILING_20D = TODAY + relativedelta(days = -20)
)

timeframes = dict(
    M1 = mt5.TIMEFRAME_M1,
    M5 = mt5.TIMEFRAME_M5,
    M15 = mt5.TIMEFRAME_M15,
    M30 = mt5.TIMEFRAME_M30,
    H1 = mt5.TIMEFRAME_H1,
    H4 = mt5.TIMEFRAME_H4,
    D1 = mt5.TIMEFRAME_D1,
    W1 = mt5.TIMEFRAME_W1,
    MN1 = mt5.TIMEFRAME_MN1
)

flags = dict(
    TRADE = mt5.COPY_TICKS_TRADE,
    INFO  = mt5.COPY_TICKS_INFO,
    ALL = mt5.COPY_TICKS_ALL
)

defaults = SimpleNamespace(
    timeframe = mt5.TIMEFRAME_D1,
    date_from =  dates['TRAILING_12M'],
    date_to = TODAY,
    flags = mt5.COPY_TICKS_ALL,
    start_pos = 0,
    count = 1000
)