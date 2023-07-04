import requests

SERVER_ADDRESS = 'http://localhost:80'
TOKEN_PATH = f'{SERVER_ADDRESS}/token'

class NotLoggedin(Exception):
    pass

class LogInError(Exception):
    pass

class Client:

    token:dict[str,str] | None = None

    def __init__(self, username:str, password:str):
        self.username = username
        self.password = password
    
    def login(self):
        credentials = f'username={self.username}&password={self.password}'
        headers = {'accept':'application/json',
                   'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(TOKEN_PATH, headers = headers, data = credentials)
        if not response.ok:
            raise LogInError(f'login failed: {response.status_code} {response.reason}')
        
        token = eval(response.content)
        token_type = token['token_type']
        access_token = token['access_token']
        token['header'] = f'{token_type} {access_token}' 
        self.token = token

    def request(self, endpoint:str):
        if self.token is None:
            raise NotLoggedin("Efetuar login")
        
        url =  f'{SERVER_ADDRESS}{endpoint}'
        query_header = {'accept':'application/json',
                        'Authorization': self.token['header']}
        response = requests.get(url, headers = query_header)
        self.last_response = response
        return response