<h1 align="center">
<img src="logo.png" width="300">

[![license](https://img.shields.io/github/license/mateuslkgouvea/marketdata?style=for-the-badge)](./LICENSE.txt)
</h1>

# About
API for MetaTrader5 data query, built with FastApi framework

# Overview
Once you set the server-side (e.g on a localhost) the api comunicates with the main MetaTrader5 functions and returns a JSON file with {"Ticker":data} format.
Most of the responses comunicate with Pandas dataframes by using pd.read_json().

## MetaTrader5
a sample request using the MetaTrader5 library:
```python
import MetaTrader5 as mt5
import datetime

mt5.copy_rates_from('PETR4', date_from = datetime(2023,1,1), date_to = datetime(2023,6,25), timeframe = mt5.TIMEFRAME_D1)
```

## marketdata API
a corresponding request on the marketdata api would be:
```python
import requests

requests.get('yourserver/mt5/rates/from/PETR4?date_from=2023-1-1&date_to=2023-6-25&timeframe=D1')
```

# Server-side
The marketdata package contained on this repository handles the server-side tasks.
To set the server on a localhost you need to define a system variable on your machine named "MT_SERVER_CONF" with the path of a JSON config file (templates are on the sample_server folder).
define the variables:

- DATA_PATH: path to store username and hashed passwords on a JSON file named records.json (can be the same as MT_SERVER_CONF path
- SECRET_KEY: randon hexadecimal variable for encryption algorythm

the server_side.py module contains a simple uvicorn instruction to run the API on the desired IP and Port.

## Security
marketdata uses a password flow handled by FastApi OAuth2 scheme, the user trying to access the protected api can user the Client class on the client_side.py module. The Client class handles the login request, token info and request headers to make things easy e.g.:

```python
from client_side import Client

client = Client('example_user', 'user_password')
client.login()
client.request('/mt5/rates/from/PETR4')
```
