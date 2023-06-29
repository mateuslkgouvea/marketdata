import pandas as pd
import requests

rates_tests = ["http://127.0.0.1:8000/rates/range/['PETR4','TTEN3']?date_from=2023-2-2&date_to=2023-2-22&timeframe=M1",
         "http://127.0.0.1:8000/rates/range/['PETR4']?date_to=2023-2-22&timeframe=M15",
         "http://127.0.0.1:8000/rates/range/VALE3?timeframe=MN1",
         "http://127.0.0.1:8000/rates/range/VALE3",
         "http://127.0.0.1:8000/rates/range/['TTEN3']"
]

ticks_tests = ["http://127.0.0.1:8000/ticks/range/['PETR4','TTEN3']?date_from=2023-6-27&date_to=2023-6-28&flags=ALL"]

def test(request):
    ans = requests.get(request).json()
    for k, v in ans.items():
        ans[k] = pd.read_json(v)
    if all([isinstance(v, pd.DataFrame) for v in ans.values()]):
        return True
    
for request in rates_tests:
    if not test(request):
        print(f'failed with request {request}')
    else:
        print('passed rates test')

    
for request in ticks_tests:
    if not test(request):
        print(f'failed with request {request}')
    else:
        print('passed ticks test')
