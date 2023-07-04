import os
import json

class MisisngEnvVariable(Exception):
    pass

class MissingServerSetting(Exception):
    pass

if "MD_SERVER_CONF" not in os.environ:
    raise MisisngEnvVariable(\
        f'define json config file path on variable MD_SERVER_CONF')

config_path = os.environ['MD_SERVER_CONF']
with open(config_path, 'r') as file:
    config = json.load(file)

exp_settings = ['SECRET_KEY', 'DATA_PATH']
check = all([True if v in config.keys() else False for v in exp_settings])

if not check:
    raise MissingServerSetting(f'ensure settings {exp_settings} are on ')

from .core import app