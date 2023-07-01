import requests
import json


token_path = 'http://127.0.0.1:8000/token'
username = 'example_user'
password = 'password'

def login(username:str, password:str):
    credentials = f'username={username}&password={password}'
    headers = {'accept':'application/json',
               'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(token_path, headers = headers, data = credentials)
    if not response.ok:
        print(f'login failed: {response.status_code} {response.reason}')
        return
    
    token_info = eval(response.content)
    token_type = token_info['token_type']
    token = token_info['access_token']
    token_info['header'] = f'{token_type} {token}' 
    return token_info


def api_request(endpoint:str, token:str):
    query_header = {'accept':'application/json',
                    'Authorization': token['header']}
    response = requests.get(endpoint, headers = query_header)
    return response


endpoint = 'http://127.0.0.1:8000/mt5/rates/range/PETR4'
token = login(username, password)
response = api_request(endpoint, token)
print(response.__dict__)
