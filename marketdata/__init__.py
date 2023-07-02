import os

variables = ['MD_DATA_PATH', 'MD_SERVER_KEY']
check = all([True if v in os.environ else False for v in variables])

if not check:
    raise KeyError(f'define system variables:{variables}')

from .core import app